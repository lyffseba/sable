using UnityEngine;

namespace Sable
{
    /// Latest AimSample mailbox. HID fire peeks. Camera never writes on click.
    public class AimBus : MonoBehaviour
    {
        public static AimBus I { get; private set; }

        AimSample _latest;

        void Awake()
        {
            if (I != null && I != this)
            {
                Destroy(gameObject);
                return;
            }
            I = this;
            _latest.uv = new Vector2(0.5f, 0.5f);
        }

        public void Publish(AimSample sample) => _latest = sample;

        public AimSample Peek() => _latest;

        public AimSample Fire() => _latest;
    }
}
