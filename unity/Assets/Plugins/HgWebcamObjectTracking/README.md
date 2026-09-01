# Hydrargyrum Games Webcam-Based Object-Tracking Solution 

⚜⚜ In the memmory of my cousin, **Pouya Hashemzade** who inspired me to learn programming in the first place! I owe a lot of what I've been able to achieve today to him; May him Rest in peace! 

⚜ Product Showcase Video: (Copyright Text added only for Video purposes, not present in Final Product!)

https://user-images.githubusercontent.com/102142095/159729964-4d57a2d7-b957-4c1a-acca-647b781c28e6.mp4

⚜ **Hydrargyrum Games Object Tracker** is a full-fledged open-source object tracking software built around Unity's ComputeShader technology that uses the Luminance difference of the object & backgrounds color to determine the screen-space position of an object; The ease of use & code accessibility that this software grants over all it's main components, makes it probably one of the main few solutions in the field worth checking out! 

⚜ As indicated by the Github page, this product is released under the **Mozilla Public License Version 2.0**, which allows any contributions to freely comit to the source code, while also prohibiting any use of this software without mentioning its author/ source; For Individuals interested in implementing this product in comericial usecases, The name of our company "Hydrargyrum Games" must be mentioned as the creator of this software; 

⚜ Our product is an independent, completely transparent, open-source & customizable object-tracking solution which does not rely on any 3rd part tools such as “OpenCV” or any other similar libraries to work. The product is expected to work on all platforms supporting ComputeShaders and only requires a Unity compatible Webcam to track the approximate screen-space position of an object! 

⚜ Please note that this product requires a "Color Picker/ Eyedropper" tool if the Luma color is expected to be changed during runtime; (The Unity editor color picker works just fine in the Editor, and this recombination is only for runtime uses only) 

⚜ Noted below are the main features of our product:
 <br>     🏅 Easy access to any webcam device equipped on your device by simply using its Name or Index.
 <br>     🏅 Capable of Tracking an unlimited number of objects. (Limited only by the device's compute power)
 <br>     🏅 Capable of Tracking Objects in both the Update() and Lateupdate() loops for framerate dependant works, While also being capable of tracking objects in the FixedUpdate() loop for Physics based projects.
 <br>     🏅 Individual settings menus for each of the trackers in your scene offering full control over theirproperties.
 <br>     🏅 Capable of tracking objects with any key color assuming that it's different from the background's.
 <br>     🏅 Events for a tracker object entering, hovering over and exiting the view of your webcam for ease of use.
 <br>     🏅 Advanced visualization shader capable of drawing an unlimited amount of trackers on your screen.
 <br>     🏅 Userfriendly and fairly straightforward to use. 

⚜Support & Documentation:
<br>     🔱 For any issues with the product, please consider making a "Github issue" for it to be solved in the next update!
<br>     🔱 For documentation on how to use the product, please check out the Documentation.pdf file located in the Documentation folder!
<br>     🔱 If you need any help with using any part of the software, please consider contacting me at khaleghisadra10@gmail.com 