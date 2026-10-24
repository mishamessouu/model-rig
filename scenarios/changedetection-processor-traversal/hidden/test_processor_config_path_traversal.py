#!/usr/bin/env python3

# model-rig adaptation of upstream's test file from fix commit
# acc4533f517b9b2fd16b96544d0ed96d2f4f0dc3 (changedetection.io, Apache-2.0).
# Changes, each also marked where it happens:
# - Dropped TestWatchConfigPathContainment. It calls
#   difference_detection_processor._resolve_watch_config_path(), a private
#   helper that the fix adds, so it names the fix's shape, not the hole.
# - test_traversing_processor_name_writes_nothing: the write check now also
#   asserts that the escape folder stays empty, and the "returns False"
#   assertion is gone. A fix that refuses by raising, or that contains the
#   path and returns quietly (as upstream's own base.py layer does), closes
#   the hole too. The write is the vulnerability; the return value is not.
# - test_traversing_processor_is_not_stored: a fix that refuses the whole
#   watch (add_watch raises or returns None) also stores nothing, so it
#   passes.
# - Added tests, marked "model-rig addition": an absolute processor name
#   with no "..", for the write and for add_watch. os.path.join() drops the
#   watch folder for an absolute name, so a ".." blocklist does not close
#   the hole. Without them a ".." blocklist scored as a full fix.

# run from dir above changedetectionio/ dir
# python3 -m unittest changedetectionio.tests.unit.test_processor_config_path_traversal

"""Regression tests for GHSA-mh42-m7cg-49fr - arbitrary file write via the watch `processor` field.

A watch's `processor` is enum-validated by the API, but /imports/import puts
request.values.get('processor') into the watch verbatim. save_processor_config() then uses that
value as a filename (f'{processor}.json') and update_extra_watch_config() did
os.path.join(data_dir, filename) + open(filepath, 'w') with no containment - so a value like
'../../../../tmp/pwned' escaped the watch directory and wrote an attacker-named JSON file
anywhere the app user could reach. get_extra_watch_config() had the same traversal on read.

Three layers are asserted here: path containment in base.py (the security boundary), the filename
sanity check in save_processor_config(), and add_watch() refusing to persist an unknown processor
at all - which also covers the share-link import path, where 'processor' arrives in JSON fetched
from a remote URL.
"""

import os
import tempfile
import unittest


class TestSaveProcessorConfigRejectsUnsafeNames(unittest.TestCase):
    """Second layer: the processor name is sanitised before it becomes a filename."""

    def setUp(self):
        from changedetectionio.store import ChangeDetectionStore
        self.datastore_path = tempfile.mkdtemp()
        self.store = ChangeDetectionStore(datastore_path=self.datastore_path,
                                          include_default_watches=False)

    def tearDown(self):
        self.store.stop_thread = True

    # model-rig: a refusal by exception counts as a refusal.
    def _save(self, uuid, data):
        from changedetectionio.processors import save_processor_config
        try:
            return save_processor_config(self.store, uuid, data)
        except Exception:
            return False

    def test_traversing_processor_name_writes_nothing(self):
        uuid = self.store.add_watch(url='https://example.com/x')

        # What /imports/import allows through today (no enum check on that path)
        evil_dir = tempfile.mkdtemp()
        evil_target = os.path.join(evil_dir, 'pwned')
        self.store.data['watching'][uuid]['processor'] = f'../../../..{evil_target}'

        self._save(uuid, {'marker': 'owned'})

        # Assert the file write FIRST - that is the vulnerability itself, and on unfixed code
        # this is the assertion that fires (naming the escaped path in the failure message).
        self.assertFalse(os.path.exists(f'{evil_target}.json'),
                         f"GHSA-mh42-m7cg-49fr: wrote outside the datastore to {evil_target}.json")
        # model-rig: nothing at all lands in the folder outside the datastore.
        self.assertEqual(os.listdir(evil_dir), [])
        # model-rig: upstream's assertFalse(ok) is dropped, see the top of the file.

    # model-rig addition: an absolute name with no "..".
    def test_absolute_processor_name_writes_nothing(self):
        uuid = self.store.add_watch(url='https://example.com/x')
        evil_dir = tempfile.mkdtemp()
        evil_target = os.path.join(evil_dir, 'pwned')
        self.store.data['watching'][uuid]['processor'] = evil_target

        self._save(uuid, {'marker': 'owned'})

        self.assertFalse(os.path.exists(f'{evil_target}.json'),
                         f"wrote outside the datastore to {evil_target}.json")
        self.assertEqual(os.listdir(evil_dir), [])

    def test_legitimate_processor_name_still_saves(self):
        from changedetectionio.processors import save_processor_config

        uuid = self.store.add_watch(url='https://example.com/x')
        self.store.data['watching'][uuid]['processor'] = 'text_json_diff'

        self.assertTrue(save_processor_config(self.store, uuid, {'marker': 'fine'}))

        written = os.path.join(self.store.data['watching'][uuid].data_dir, 'text_json_diff.json')
        self.assertTrue(os.path.isfile(written), "the legitimate config write must still happen")




class TestAddWatchRejectsUnknownProcessor(unittest.TestCase):
    """Third layer: an unknown processor never gets persisted in the first place.

    add_watch() is the chokepoint for the two callers that don't enum-validate: /imports/import
    (request.values verbatim) and the share-link path, which takes 'processor' out of JSON
    fetched from a remote URL.
    """

    def setUp(self):
        from changedetectionio.store import ChangeDetectionStore
        self.datastore_path = tempfile.mkdtemp()
        self.store = ChangeDetectionStore(datastore_path=self.datastore_path,
                                          include_default_watches=False)

    def tearDown(self):
        self.store.stop_thread = True

    # model-rig: refusing the whole watch (raise or None) also stores nothing.
    def _stored_processor(self, processor):
        try:
            uuid = self.store.add_watch(url='https://example.com/x',
                                        extras={'processor': processor})
        except Exception:
            return None
        if uuid is None:
            return None
        return self.store.data['watching'][uuid].get('processor')

    def test_traversing_processor_is_not_stored(self):
        self.assertNotEqual(self._stored_processor('../../../../tmp/pwned'),
                            '../../../../tmp/pwned',
                            "a path-traversing processor must not be persisted")

    # model-rig addition: an absolute name with no "..".
    def test_absolute_processor_is_not_stored(self):
        self.assertNotEqual(self._stored_processor('/tmp/pwned'), '/tmp/pwned',
                            "an absolute-path processor must not be persisted")

    def test_known_processor_is_kept(self):
        uuid = self.store.add_watch(url='https://example.com/x',
                                    extras={'processor': 'restock_diff'})
        self.assertEqual(self.store.data['watching'][uuid].get('processor'), 'restock_diff')


if __name__ == '__main__':
    unittest.main()
