using UnityEngine;

namespace Sable
{
    /// Hg luma tracker → AimSample. Thing in the webcam is the pointer.
    /// No YOLO. Pick a luma that is not the desk.
    [RequireComponent(typeof(AimBus))]
    public class HgAimSource : MonoBehaviour
    {
        public HgTracker tracker;
        public int trackerIndex;
        public bool forceGun;
        public bool desktop;

        const float HidIdleMs = 40f;
        float _hidLast = -999f;
        Vector3 _lastMouse;
        AimBus _bus;

        void Awake()
        {
            _bus = GetComponent<AimBus>();
            _lastMouse = Input.mousePosition;
        }

        void Update()
        {
            if ((Input.mousePosition - _lastMouse).sqrMagnitude > 0.25f)
                _hidLast = Time.unscaledTime * 1000f;
            _lastMouse = Input.mousePosition;
            if (Input.GetKey(KeyCode.Space)) forceGun = true;
            if (Input.GetKeyUp(KeyCode.Space)) forceGun = false;
            if (Input.GetKeyDown(KeyCode.T)) desktop = !desktop;

            var sample = new AimSample { tHw = (long)(Time.realtimeSinceStartupAsDouble * 1e6) };

            if (desktop)
            {
                var p = Input.mousePosition;
                sample.uv = new Vector2(p.x / Mathf.Max(1, Screen.width), p.y / Mathf.Max(1, Screen.height));
                sample.valid = true;
                sample.lifted = true;
                sample.confidence = 1f;
                _bus.Publish(sample);
                return;
            }

            sample.uv = new Vector2(0.5f, 0.5f);
            if (tracker == null || tracker.Trackers == null || tracker.Trackers.Length <= trackerIndex)
            {
                _bus.Publish(sample);
                return;
            }

            var pod = tracker.Trackers[trackerIndex];
            var pos = pod.SmoothedPosition;
            sample.uv = new Vector2(Mathf.Clamp01(pos.x), Mathf.Clamp01(pos.y));
            sample.valid = pod.Is_Visible;
            sample.confidence = pod.Is_Visible ? 0.85f : 0.1f;
            var hidMoving = (Time.unscaledTime * 1000f - _hidLast) < HidIdleMs;
            sample.lifted = forceGun || !hidMoving;
            _bus.Publish(sample);
        }
    }
}
