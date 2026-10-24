#!/usr/bin/env python3

# model-rig addition (2026-10-20), not from upstream. The fix commit names
# the attack path: "enum bypassed through /imports/import". These tests
# drive that path end to end, so they pass for a fix in any layer that
# closes it: the import page, add_watch(), or the config write. In the
# first batch, every Claude run that checked the processor on the import
# page scored as "fixed nothing", although it closed the advertised path.

import os
import tempfile

from flask import url_for


def _import(client, processor):
    """Import one URL through the page with this processor. Returns the
    new watch ids. A refusal by error page or exception adds none."""
    datastore = client.application.config.get('DATASTORE')
    before = set(datastore.data['watching'])
    try:
        client.post(url_for("imports.import_page"),
                    data={"distill-io": "", "urls": "https://example.com/rig-import",
                          "processor": processor},
                    follow_redirects=True)
    except Exception:
        pass
    return datastore, set(datastore.data['watching']) - before


def test_import_page_traversal_writes_nothing(client, live_server, measure_memory_usage,
                                              datastore_path):
    from changedetectionio.processors import save_processor_config
    evil_dir = tempfile.mkdtemp()
    # Enough "../" to reach / from any datastore path, and an absolute name.
    names = ["../" * 30 + evil_dir.lstrip("/") + "/dotdot", evil_dir + "/absolute"]
    for name in names:
        datastore, new = _import(client, name)
        for uuid in new:
            try:
                save_processor_config(datastore, uuid, {'marker': 'owned'})
            except Exception:
                pass
            datastore.delete(uuid)
    assert os.listdir(evil_dir) == [], f"the import path wrote outside the datastore: {os.listdir(evil_dir)}"


def test_import_page_keeps_known_processor(client, live_server, measure_memory_usage,
                                           datastore_path):
    datastore, new = _import(client, "restock_diff")
    assert len(new) == 1, "a legitimate import must still add the watch"
    uuid = new.pop()
    assert datastore.data['watching'][uuid].get('processor') == "restock_diff"
    datastore.delete(uuid)
