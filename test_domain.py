import unittest
from core import Store, Problem, instant
from domain import dispatch

class VideoTests(unittest.TestCase):
    def setUp(self):
        self.store = Store(); self.now = instant('2026-10-09T15:00:00Z')
    def tearDown(self): self.store.close()
    def call(self, path, **data): return self.store.transact(lambda s: dispatch(s, 'POST', path, data, self.now))
    def campaign(self, pieces):
        self.call('/campaigns', actor='brand', id='c1', required_pieces=pieces)
        self.call('/deliveries', actor='creator', id='d1', campaign_id='c1')
    def version(self, piece='video', previous=0):
        return self.call('/deliveries/d1/pieces/' + piece + '/versions', actor='creator', url='https://example.org/video.mp4', duration_seconds=60, previous_version=previous)
    def approve_piece(self, piece='video', version=1):
        return self.call(f'/deliveries/d1/pieces/{piece}/versions/{version}/approve', actor='brand')
    def approve(self): return self.call('/deliveries/d1/approve', actor='brand')
    def test_required_pieces_block_delivery_approval(self):
        self.campaign(['video', 'script', 'cover', 'caption'])
        self.version(); self.approve_piece()
        with self.assertRaisesRegex(Problem, 'script, cover, caption'): self.approve()
        for piece in ['script', 'cover', 'caption']: self.version(piece); self.approve_piece(piece)
        self.assertEqual(self.approve()['state'], 'approved')
    def test_video_only_does_not_require_script_or_optional_cover(self):
        self.campaign(['video']); self.version(); self.version('cover'); self.approve_piece()
        self.assertEqual(self.approve()['state'], 'approved')
    def test_new_required_version_revokes_and_reapproval_restores(self):
        self.campaign(['video']); self.version(); self.approve_piece(); self.approve()
        result = self.version(previous=1)
        self.assertEqual(result['state'], 'in_production')
        self.assertTrue(result['pieces']['video'][0]['approved'])
        with self.assertRaises(Problem): self.approve()
        self.assertEqual(self.approve_piece(version=2)['state'], 'approved')
    def test_comment_stays_on_its_version(self):
        self.campaign(['video']); self.version()
        self.call('/deliveries/d1/pieces/video/versions/1/comments', actor='brand', second=12.5, text='Cut this pause')
        result = self.version(previous=1)
        self.assertEqual(result['pieces']['video'][0]['comments'][0]['second'], 12.5)
        self.assertEqual(result['pieces']['video'][1]['comments'], [])
    def test_stale_approval_and_stale_upload_are_rejected(self):
        self.campaign(['video']); self.version(); self.version(previous=1)
        with self.assertRaises(Problem): self.approve_piece(version=1)
        with self.assertRaises(Problem): self.version(previous=1)
    def test_comment_bounds_and_nonfinite_values(self):
        self.campaign(['video']); self.version()
        for second in [-1, 61, float('nan'), float('inf'), True]:
            with self.subTest(second=second), self.assertRaises(Problem):
                self.call('/deliveries/d1/pieces/video/versions/1/comments', actor='brand', second=second, text='Test')
    def test_optional_new_version_does_not_revoke_required_approval(self):
        self.campaign(['video']); self.version(); self.approve_piece(); self.approve()
        self.assertEqual(self.version('cover')['state'], 'approved')
    def test_roles_enforced_at_domain_boundary(self):
        self.campaign(['video']); self.version()
        with self.assertRaises(Problem): self.call('/deliveries/d1/pieces/video/versions/1/approve', actor='creator')

if __name__ == '__main__': unittest.main()
