from pytest import raises

import os
import datetime

from dateutil import tz
from pushsource import Source, FilePushItem, ChannelDumpPushItem


DATADIR = os.path.join(os.path.dirname(__file__), "data")


def test_staged_incomplete_channel_dumps():
    staged_dir = os.path.join(DATADIR, "incomplete_channel_dumps")
    source = Source.get("staged:" + staged_dir)

    with raises(ValueError) as exc_info:
        list(source)

    assert (
        "missing mandatory attribute 'channel_dump_disc_number' for "
        "somedest/CHANNEL_DUMPS/myfile.txt"
    ) in str(exc_info.value)


def test_staged_nometa_channel_dumps(tmpdir):
    staged_dir = tmpdir.mkdir("staged")
    staged_dir.mkdir("dest").mkdir("CHANNEL_DUMPS").join("testfile").write("test")
    staged_dir.join("staged.json").write('{"header": {"version": "0.2"}}')

    source = Source.get("staged:%s" % staged_dir)

    with raises(ValueError) as exc_info:
        list(source)

    assert "staged.json doesn't contain data for dest/CHANNEL_DUMPS/testfile" in str(
        exc_info.value
    )


def test_staged_channel_dumps():
    staged_dir = os.path.join(DATADIR, "simple_channel_dumps")
    source = Source.get("staged:" + staged_dir)

    files = list(source)

    files.sort(key=lambda item: item.src)

    # It should load all the expected files with fields filled in by metadata
    assert files == [
        ChannelDumpPushItem(
            name="myfile.txt",
            state="PENDING",
            src=os.path.join(staged_dir, "somedest/CHANNEL_DUMPS/myfile.txt"),
            dest=["somedest"],
            md5sum=None,
            sha256sum="9481d6638081ff26556e09844ae1fbf680ad83fb98afa2f3f88718537b41f8b9",
            origin="staged",
            build=None,
            signing_key=None,
            description="test channel dump 1",
            arch="x86_64",
            eng_product_ids=[1, 2, 3],
            content="some content",
            datetime=datetime.datetime(2020, 2, 19, 11, 5, tzinfo=tz.tzutc()),
            disk_number=1,
            channels=["ch1", "ch2"],
            product_name="a product",
            product_version="ABCD",
            type="base",
        ),
        ChannelDumpPushItem(
            name="otherfile.txt",
            state="PENDING",
            src=os.path.join(staged_dir, "somedest/CHANNEL_DUMPS/otherfile.txt"),
            dest=["somedest"],
            md5sum=None,
            sha256sum="64f31e7083a2bdbdefa86bbe23de536133bee35980353312ad010b3fcc6a13c4",
            origin="staged",
            build=None,
            signing_key=None,
            description="test channel dump 2",
            arch="i686",
            eng_product_ids=[2, 3, 4],
            content="other content",
            datetime=datetime.datetime(2020, 2, 19, 11, 50, tzinfo=tz.tzutc()),
            disk_number=2,
            channels=["ch3", "ch4"],
            product_name="other product",
            product_version="DEF",
            type="incremental",
        ),
    ]
