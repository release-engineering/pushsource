import json
import logging
import os

import pytest
import requests

from pushsource import (
    AmiAccessEndpointUrl,
    AmiBillingCodes,
    AmiPushItem,
    AmiRelease,
    Source,
    AmiSecurityGroup,
)

DATAPATH = os.path.join(os.path.dirname(__file__), "data")


def make_response(task_id):
    with open(os.path.join(DATAPATH, str(task_id), "images.json")) as f:
        return json.load(f)


def test_get_ami_push_items_single_task(requests_mock):
    """
    Tests getting push item from one Pub task.
    """
    # test setup
    task_id = 123456
    pub_url = "https://pub.example.com"
    request_url = os.path.join(
        pub_url, "pub/task", str(task_id), "log/images.json?format=raw"
    )

    requests_mock.register_uri("GET", request_url, json=make_response(task_id))

    # request push items from source
    with Source.get("pub:%s" % pub_url, task_id=task_id) as source:
        push_items = [item for item in source]

    # there should be exactly one  push item
    assert len(push_items) == 1

    # with following content
    assert push_items == [
        AmiPushItem(
            name="RHEL-SAP-8.4.0_HVM-20230109-x86_64-0-Hourly2-GP2",
            state="PENDING",
            src="/fake/path/aws/sa-east-1-hourly/AWS_IMAGES/rhel-sap-ec2-8.4-20220802.sp.10.x86_64.raw",
            dest=["sa-east-1-hourly"],
            md5sum=None,
            sha256sum=None,
            origin="/fake/path/aws/",
            build=None,
            build_info=None,
            signing_key=None,
            release=AmiRelease(
                product="SAP",
                date="20230109",
                arch="x86_64",
                respin=0,
                version="8.4.0",
                base_product="RHEL",
                base_version=None,
                variant="BaseOS",
                type=None,
            ),
            type="hourly",
            region="sa-east-1",
            virtualization="hvm",
            volume="gp2",
            root_device="/dev/sda1",
            description="Provided by Red Hat, Inc.",
            sriov_net_support="simple",
            ena_support=True,
            billing_codes=AmiBillingCodes(name="Hourly2", codes=["bp-fake"]),
            image_id="ami-fake-123456",
            release_notes="Fake release notes",
            usage_instructions="Fake use instructions",
            recommended_instance_type="t2.micro",
            marketplace_entity_type="AMI",
            scanning_port=10,
            user_name="Fake-Username",
            version_title="version title",
            security_groups=[
                AmiSecurityGroup(
                    from_port=10, ip_protocol="udp", ip_ranges=["8.1.8.8"], to_port=90
                ),
                AmiSecurityGroup(
                    from_port=11, ip_protocol="tcp", ip_ranges=["8.2.8.8"], to_port=91
                ),
            ],
            access_endpoint_url=AmiAccessEndpointUrl(port=10, protocol="http"),
        )
    ]


def test_get_ami_push_items_multiple_tasks(requests_mock):
    """
    Tests getting push items for multiple Pub tasks.
    """
    # test setup
    task_ids = "123456,100,200"
    pub_url = "https://pub.example.com"

    for task_id in task_ids.split(","):
        request_url = os.path.join(
            pub_url, "pub/task", task_id, "log/images.json?format=raw"
        )
        requests_mock.register_uri("GET", request_url, json=make_response(task_id))

    # request push items from push source
    with Source.get("pub:%s" % pub_url, task_id=task_ids) as source:
        push_items = [item for item in source]

    # there should be 4 items
    assert len(push_items) == 4
    # with following content
    assert sorted(push_items, key=lambda x: x.image_id) == [
        AmiPushItem(
            name="RHEL-SAP-8.4.0_HVM-20230109-x86_64-0-Hourly2-GP2",
            state="PENDING",
            src="/fake/path/aws/me-south-1-hourly/AWS_IMAGES/rhel-sap-ec2-8.4-20220802.sp.10.x86_64.raw",
            dest=["me-south-1-hourly"],
            md5sum=None,
            sha256sum=None,
            origin="/fake/path/aws",
            build=None,
            build_info=None,
            signing_key=None,
            release=AmiRelease(
                product="SAP",
                date="20230109",
                arch="x86_64",
                respin=0,
                version="8.4.0",
                base_product="RHEL",
                base_version=None,
                variant="BaseOS",
                type=None,
            ),
            type="hourly",
            region="me-south-1",
            virtualization="hvm",
            volume="gp2",
            root_device="/dev/sda1",
            description="Provided by Red Hat, Inc.",
            sriov_net_support="simple",
            ena_support=True,
            billing_codes=AmiBillingCodes(name="Hourly2", codes=["bp-fake"]),
            image_id="ami-fake-100",
            access_endpoint_url=None,
        ),
        AmiPushItem(
            name="RHEL-SAP-8.4.0_HVM-20230109-x86_64-0-Hourly2-GP2",
            state="PENDING",
            src="/fake/path/aws/sa-east-1-hourly/AWS_IMAGES/rhel-sap-ec2-8.4-20220802.sp.10.x86_64.raw",
            dest=["sa-east-1-hourly"],
            md5sum=None,
            sha256sum=None,
            origin="/fake/path/aws/",
            build=None,
            build_info=None,
            signing_key=None,
            release=AmiRelease(
                product="SAP",
                date="20230109",
                arch="x86_64",
                respin=0,
                version="8.4.0",
                base_product="RHEL",
                base_version=None,
                variant="BaseOS",
                type=None,
            ),
            type="hourly",
            region="sa-east-1",
            virtualization="hvm",
            volume="gp2",
            root_device="/dev/sda1",
            description="Provided by Red Hat, Inc.",
            sriov_net_support="simple",
            ena_support=True,
            billing_codes=AmiBillingCodes(name="Hourly2", codes=["bp-fake"]),
            image_id="ami-fake-123456",
            release_notes="Fake release notes",
            usage_instructions="Fake use instructions",
            recommended_instance_type="t2.micro",
            marketplace_entity_type="AMI",
            scanning_port=10,
            user_name="Fake-Username",
            version_title="version title",
            security_groups=[
                AmiSecurityGroup(
                    from_port=10, ip_protocol="udp", ip_ranges=["8.1.8.8"], to_port=90
                ),
                AmiSecurityGroup(
                    from_port=11, ip_protocol="tcp", ip_ranges=["8.2.8.8"], to_port=91
                ),
            ],
            access_endpoint_url=AmiAccessEndpointUrl(port=10, protocol="http"),
        ),
        AmiPushItem(
            name="RHEL-SAP-8.4.0_HVM-20230109-x86_64-0-Hourly2-GP2",
            state="PENDING",
            src="/fake/path/aws/us-east-1-hourly/AWS_IMAGES/rhel-sap-ec2-8.4-20220802.sp.10.x86_64.raw",
            dest=["us-east-1-hourly"],
            md5sum=None,
            sha256sum=None,
            origin="/fake/path/aws/",
            build=None,
            build_info=None,
            signing_key=None,
            release=AmiRelease(
                product="SAP",
                date="20230109",
                arch="x86_64",
                respin=0,
                version="8.4.0",
                base_product="RHEL",
                base_version=None,
                variant="BaseOS",
                type=None,
            ),
            type="hourly",
            region="us-east-1",
            virtualization="hvm",
            volume="gp2",
            root_device="/dev/sda1",
            description="Provided by Red Hat, Inc.",
            sriov_net_support="simple",
            ena_support=True,
            billing_codes=AmiBillingCodes(name="Hourly2", codes=["bp-fake"]),
            image_id="ami-fake-200-A",
            security_groups=[
                AmiSecurityGroup(
                    from_port=-1,
                    ip_protocol="icmpv6",
                    ip_ranges=["255.255.255.255"],
                    to_port=255,
                )
            ],
            access_endpoint_url=AmiAccessEndpointUrl(port=10, protocol="https"),
        ),
        AmiPushItem(
            name="RHEL-SAP-8.4.0_HVM-20230109-x86_64-0-Hourly2-GP2",
            state="PENDING",
            src="/fake/path/aws/me-central-1-hourly/AWS_IMAGES/rhel-sap-ec2-8.4-20220802.sp.10.x86_64.raw",
            dest=["me-central-1-hourly"],
            md5sum=None,
            sha256sum=None,
            origin="/fake/path/aws/",
            build=None,
            build_info=None,
            signing_key=None,
            release=AmiRelease(
                product="SAP",
                date="20230109",
                arch="x86_64",
                respin=0,
                version="8.4.0",
                base_product="RHEL",
                base_version=None,
                variant="BaseOS",
                type=None,
            ),
            type="hourly",
            region="me-central-1",
            virtualization="hvm",
            volume="gp2",
            root_device="/dev/sda1",
            description="Provided by Red Hat, Inc.",
            sriov_net_support="simple",
            ena_support=True,
            billing_codes=AmiBillingCodes(name="Hourly2", codes=["bp-fake"]),
            image_id="ami-fake-200-B",
            security_groups=[
                AmiSecurityGroup(
                    from_port=1, ip_protocol="icmp", ip_ranges=["1.1.1.1"], to_port=10
                )
            ],
            access_endpoint_url=AmiAccessEndpointUrl(port=10, protocol="http"),
        ),
    ]


def test_pub_source_invalid_task_id(requests_mock, caplog):
    """
    Tests behavior when invalid task id is passed to source.
    """
    # test setup
    caplog.set_level(logging.WARNING)
    task_id = "a7df9"
    pub_url = "https://pub.example.com"
    request_url = os.path.join(
        pub_url, "pub/task", "123456", "log/images.json?format=raw"
    )

    requests_mock.register_uri("GET", request_url, json=make_response(123456))

    # request push items from source
    with Source.get("pub:%s" % pub_url, task_id=task_id) as source:
        push_items = [item for item in source]

    # no exception raise but also no push items
    assert len(push_items) == 0
    # with follow line captured in log
    assert caplog.messages[0] == "Invalid Pub task ID: a7df9"


def test_pub_source_empty_response(requests_mock, caplog):
    """
    Tests behavior when empty response is received from source.
    """
    # test setup
    caplog.set_level(logging.WARNING)
    task_id = 123456
    pub_url = "https://pub.example.com"
    request_url = os.path.join(
        pub_url, "pub/task", "123456", "log/images.json?format=raw"
    )

    requests_mock.register_uri("GET", request_url, json={})

    with Source.get("pub:%s" % pub_url, task_id=task_id) as source:
        push_items = [item for item in source]

    # there are no push items returned
    assert len(push_items) == 0

    # with details captured in logged
    assert caplog.messages == ["Cannot parse AMI push item/s: {}"]


def test_pub_source_missing_task(requests_mock, caplog):
    """
    Tests query for push items for non-existing Pub task.
    """
    # test setup
    caplog.set_level(logging.WARNING)
    task_id = 1234567890
    pub_url = "https://pub.example.com"
    request_url = os.path.join(
        pub_url, "pub/task", "1234567890", "log/images.json?format=raw"
    )

    requests_mock.register_uri("GET", request_url, status_code=404)

    # request push items - 404 received raises exception
    with pytest.raises(requests.exceptions.HTTPError) as exc:
        with Source.get("pub:%s" % pub_url, task_id=task_id) as source:
            _ = [item for item in source]

    assert "404 Client Error:" in str(exc.value)
