#include "sable/capture.hpp"

#import <AVFoundation/AVFoundation.h>
#import <CoreMedia/CoreMedia.h>
#import <CoreVideo/CoreVideo.h>
#import <Foundation/Foundation.h>

#include <chrono>
#include <cmath>
#include <cstring>
#include <limits>

namespace {

std::int64_t now_us() {
	using clock = std::chrono::steady_clock;
	return std::chrono::duration_cast<std::chrono::microseconds>(clock::now().time_since_epoch())
		.count();
}

AVCaptureDevice* pick_device(const std::string& id) {
	if (!id.empty() && id != "/dev/video0" && id != "default") {
		NSString* wanted = [NSString stringWithUTF8String:id.c_str()];
		AVCaptureDevice* by_id = [AVCaptureDevice deviceWithUniqueID:wanted];
		if (by_id) {
			return by_id;
		}
	}
	return [AVCaptureDevice defaultDeviceWithMediaType:AVMediaTypeVideo];
}

AVCaptureDeviceFormat* pick_format(AVCaptureDevice* dev, int w, int h) {
	AVCaptureDeviceFormat* best = nil;
	int best_score = std::numeric_limits<int>::max();
	for (AVCaptureDeviceFormat* fmt in dev.formats) {
		const CMVideoDimensions dim = CMVideoFormatDescriptionGetDimensions(fmt.formatDescription);
		const int score = std::abs(static_cast<int>(dim.width) - w) +
						  std::abs(static_cast<int>(dim.height) - h);
		if (score < best_score) {
			best_score = score;
			best = fmt;
		}
	}
	return best;
}

sable::FrameBuffer copy_pixel_buffer(CVPixelBufferRef px, std::int64_t t_hw) {
	sable::FrameBuffer frame;
	if (!px) {
		return frame;
	}
	CVPixelBufferLockBaseAddress(px, kCVPixelBufferLock_ReadOnly);
	const OSType fmt = CVPixelBufferGetPixelFormatType(px);
	const size_t w = CVPixelBufferGetWidth(px);
	const size_t h = CVPixelBufferGetHeight(px);
	const size_t stride = CVPixelBufferGetBytesPerRow(px);
	const auto* base = static_cast<const std::uint8_t*>(CVPixelBufferGetBaseAddress(px));
	if (!base || w == 0 || h == 0) {
		CVPixelBufferUnlockBaseAddress(px, kCVPixelBufferLock_ReadOnly);
		return frame;
	}
	if (fmt == kCVPixelFormatType_32BGRA) {
		frame.format = sable::PixelFormat::Bgra32;
	} else if (fmt == kCVPixelFormatType_422YpCbCr8_yuvs) {
		frame.format = sable::PixelFormat::Yuy2;
	} else {
		CVPixelBufferUnlockBaseAddress(px, kCVPixelBufferLock_ReadOnly);
		return frame;
	}
	frame.width = static_cast<int>(w);
	frame.height = static_cast<int>(h);
	frame.stride = static_cast<int>(stride);
	frame.t_hw = t_hw;
	const size_t n = stride * h;
	frame.bytes.resize(n);
	std::memcpy(frame.bytes.data(), base, n);
	CVPixelBufferUnlockBaseAddress(px, kCVPixelBufferLock_ReadOnly);
	return frame;
}

} // namespace

@interface SableAvfSink : NSObject <AVCaptureVideoDataOutputSampleBufferDelegate>
@property(nonatomic, assign) sable::AvfCapture* owner;
@end

@implementation SableAvfSink
- (void)captureOutput:(AVCaptureOutput*)output
	didOutputSampleBuffer:(CMSampleBufferRef)sampleBuffer
		   fromConnection:(AVCaptureConnection*)connection {
	(void)output;
	(void)connection;
	if (_owner) {
		_owner->on_sample_buffer(sampleBuffer);
	}
}
@end

namespace sable {

void AvfCapture::on_sample_buffer(void* sample_buffer) {
	CMSampleBufferRef sb = static_cast<CMSampleBufferRef>(sample_buffer);
	if (!sb) {
		return;
	}
	CVPixelBufferRef px = CMSampleBufferGetImageBuffer(sb);
	FrameBuffer frame = copy_pixel_buffer(px, now_us());
	if (frame.bytes.empty()) {
		return;
	}
	publish(frame);
}

bool AvfCapture::start(const CaptureConfig& cfg) {
	backend_ = "avf";
	return CaptureThread::start(cfg);
}

void AvfCapture::run() {
	@autoreleasepool {
		AVAuthorizationStatus auth = [AVCaptureDevice authorizationStatusForMediaType:AVMediaTypeVideo];
		if (auth == AVAuthorizationStatusNotDetermined) {
			dispatch_semaphore_t sem = dispatch_semaphore_create(0);
			[AVCaptureDevice requestAccessForMediaType:AVMediaTypeVideo
									 completionHandler:^(BOOL granted) {
										 (void)granted;
										 dispatch_semaphore_signal(sem);
									 }];
			dispatch_semaphore_wait(sem, DISPATCH_TIME_FOREVER);
			auth = [AVCaptureDevice authorizationStatusForMediaType:AVMediaTypeVideo];
		}
		if (auth != AVAuthorizationStatusAuthorized) {
			error_ = "camera permission denied";
			backend_ = "dummy";
			while (!stop_) {
				std::this_thread::sleep_for(std::chrono::milliseconds(20));
			}
			return;
		}

		AVCaptureDevice* dev = pick_device(cfg_.device);
		if (!dev) {
			error_ = "no AVFoundation camera";
			backend_ = "dummy";
			while (!stop_) {
				std::this_thread::sleep_for(std::chrono::milliseconds(20));
			}
			return;
		}

		NSError* err = nil;
		AVCaptureDeviceInput* input = [AVCaptureDeviceInput deviceInputWithDevice:dev error:&err];
		if (!input) {
			error_ = err ? std::string([[err localizedDescription] UTF8String]) : "device input failed";
			backend_ = "dummy";
			while (!stop_) {
				std::this_thread::sleep_for(std::chrono::milliseconds(20));
			}
			return;
		}

		AVCaptureSession* session = [[AVCaptureSession alloc] init];
		session.sessionPreset = AVCaptureSessionPreset640x480;
		if (![session canAddInput:input]) {
			error_ = "cannot add camera input";
			backend_ = "dummy";
			while (!stop_) {
				std::this_thread::sleep_for(std::chrono::milliseconds(20));
			}
			return;
		}
		[session addInput:input];

		if ([dev lockForConfiguration:&err]) {
			AVCaptureDeviceFormat* fmt = pick_format(dev, cfg_.width, cfg_.height);
			if (fmt) {
				dev.activeFormat = fmt;
			}
			const int fps = cfg_.fps > 0 ? cfg_.fps : 30;
			CMTime duration = CMTimeMake(1, fps);
			dev.activeVideoMinFrameDuration = duration;
			dev.activeVideoMaxFrameDuration = duration;
			if (cfg_.lock_exposure && [dev isExposureModeSupported:AVCaptureExposureModeLocked]) {
				dev.exposureMode = AVCaptureExposureModeLocked;
				exposure_locked_ = true;
			}
			if (cfg_.lock_awb && [dev isWhiteBalanceModeSupported:AVCaptureWhiteBalanceModeLocked]) {
				dev.whiteBalanceMode = AVCaptureWhiteBalanceModeLocked;
			}
			[dev unlockForConfiguration];
		}

		AVCaptureVideoDataOutput* output = [[AVCaptureVideoDataOutput alloc] init];
		output.alwaysDiscardsLateVideoFrames = YES;
		output.videoSettings = @{
			(id)kCVPixelBufferPixelFormatTypeKey : @(kCVPixelFormatType_32BGRA),
		};
		if (![session canAddOutput:output]) {
			error_ = "cannot add video output";
			backend_ = "dummy";
			while (!stop_) {
				std::this_thread::sleep_for(std::chrono::milliseconds(20));
			}
			return;
		}
		[session addOutput:output];

		SableAvfSink* sink = [[SableAvfSink alloc] init];
		sink.owner = this;
		dispatch_queue_t q = dispatch_queue_create("sable.cv_input.avf", DISPATCH_QUEUE_SERIAL);
		[output setSampleBufferDelegate:sink queue:q];

		backend_ = "avf-bgra";
		[session startRunning];

		while (!stop_) {
			std::this_thread::sleep_for(std::chrono::milliseconds(5));
		}

		[session stopRunning];
		[output setSampleBufferDelegate:nil queue:nil];
		sink.owner = nil;
	}
}

} // namespace sable
