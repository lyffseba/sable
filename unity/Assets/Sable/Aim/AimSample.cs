namespace Sable
{
    /// Shared aim contract. Fire peeks this. It never waits on a camera frame.
    public struct AimSample
    {
        public UnityEngine.Vector2 uv;
        public bool valid;
        public bool lifted;
        public float confidence;
        public long tHw;
    }
}
