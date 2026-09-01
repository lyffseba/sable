using UnityEngine;
using UnityEngine.UI;

namespace Sable
{
    /// 30s booth. Crosshair follows AimSample.uv. Click peeks the bus.
    public class RangeLoop : MonoBehaviour
    {
        public AimBus bus;
        public HidFire hid;
        public RectTransform crosshair;
        public Text scoreLabel;
        public Text chip;

        const float PadEnd = 3f;
        const float GunEnd = 27f;
        const float LoopEnd = 30f;

        float _elapsed;
        int _score;
        enum Phase { Pad, Gun, Drop }
        Phase _phase = Phase.Pad;

        void Awake()
        {
            if (bus == null) bus = AimBus.I;
            if (hid == null) hid = GetComponent<HidFire>();
            Cursor.visible = false;
        }

        void OnDestroy() => Cursor.visible = true;

        void Update()
        {
            _elapsed = Mathf.Min(LoopEnd, _elapsed + Time.deltaTime);
            if (_phase != Phase.Drop && _elapsed >= GunEnd) _phase = Phase.Drop;
            else if (_phase == Phase.Pad && _elapsed >= PadEnd && bus.Peek().lifted)
                _phase = Phase.Gun;

            var s = bus.Peek();
            if (crosshair != null)
            {
                var canvas = crosshair.parent as RectTransform;
                if (canvas != null)
                    crosshair.anchoredPosition = new Vector2(
                        (s.uv.x - 0.5f) * canvas.rect.width,
                        (s.uv.y - 0.5f) * canvas.rect.height);
            }

            if (Input.GetMouseButtonDown(0))
            {
                var shot = hid.Shot();
                if (_phase != Phase.Drop && shot.lifted) _score++;
            }

            if (scoreLabel) scoreLabel.text = "SCORE  " + _score;
            if (chip) chip.text = _phase == Phase.Pad ? "PAD" : _phase == Phase.Gun ? "GUN" : "DROP";
        }
    }
}
