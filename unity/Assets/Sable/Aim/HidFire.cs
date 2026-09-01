using UnityEngine;

namespace Sable
{
    /// Click is HID against the latest AimSample. Never wait for a camera frame.
    public class HidFire : MonoBehaviour
    {
        public AimBus bus;

        public AimSample Shot()
        {
            if (bus == null) bus = AimBus.I;
            return bus != null ? bus.Fire() : default;
        }
    }
}
