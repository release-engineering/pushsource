from pushsource import Source, ErratumPushItem, ErratumReference


def test_errata_typical_metadata(fake_errata_tool):
    """Test fetching an advisory with no files:

    - it is not necessary to provide a koji source
    - returns ErratumPushItem with appropriate content
    """

    source = Source.get("errata:https://errata.example.com?errata=RHBA-2020:0518")

    # It should not have tried to access ET yet (lazy fetching)
    assert not fake_errata_tool.last_url

    # Load all items
    items = list(source)

    # It should have queried the expected XML-RPC endpoint.
    # Note that our https was replaced with http, this is expected!
    assert (
        fake_errata_tool.last_url == "http://errata.example.com/errata/errata_service"
    )

    # It should have loaded that one advisory
    assert len(items) == 1

    # The advisory object should be initialized with all the right fields
    assert items[0] == ErratumPushItem(
        name="RHBA-2020:0518",
        state="PENDING",
        src=None,
        dest=[
            "rhel-7-server-devtools-rpms__x86_64",
            "rhel-7-server-for-power-le-devtools-rpms__ppc64le",
            "rhel-7-server-for-system-z-devtools-rpms__s390x",
        ],
        content_types=["docker"],
        from_="release-engineering@redhat.com",
        rights="Copyright 2020 Red Hat Inc",
        title="updated devtools/rust-toolset-rhel7 container image",
        updated="2020-02-17 09:14:49 UTC",
        issued="2020-02-17 09:14:49 UTC",
        severity="None",
        summary=(
            "Updated devtools/rust-toolset-rhel7 container image is now available "
            "for Red Hat Developer Tools."
        ),
        solution=(
            "The Red Hat Developer Tools container image provided by this update "
            "can be downloaded from the Red Hat Container Registry at registry.access.redhat.com. "
            "Installation instructions for your platform are available at Red Hat Container "
            "Catalog (see References).\n\nDockerfiles and scripts should be amended either to "
            "refer to this new image specifically, or to the latest image generally."
        ),
        description=(
            "The devtools/rust-toolset-rhel7 container image has been updated for Red "
            "Hat Developer Tools to address the following security advisory: RHSA-2020:0374 "
            "(see References)\n\nUsers of devtools/rust-toolset-rhel7 container images are "
            "advised to upgrade to these updated images, which contain backported patches to "
            "correct these security issues, fix these bugs and add these enhancements. Users of "
            "these images are also encouraged to rebuild all container images that depend on these "
            "images.\n\nYou can find images updated by this advisory in Red Hat Container Catalog "
            "(see References)."
        ),
        references=[
            ErratumReference(
                href="https://access.redhat.com/errata/RHBA-2020:0518",
                id="RHBA-2020:0518",
                title="RHBA-2020:0518",
                type="self",
            ),
            ErratumReference(
                href="https://bugzilla.redhat.com/show_bug.cgi?id=1744149",
                id="1744149",
                title="CVE-2019-14816 kernel: heap overflow in mwifiex_update_vs_ie() function of Marvell WiFi driver",
                type="bugzilla",
            ),
            ErratumReference(
                href="https://bugzilla.redhat.com/show_bug.cgi?id=1771909",
                id="1771909",
                title="CVE-2019-17133 kernel: buffer overflow in cfg80211_mgd_wext_giwessid in net/wireless/wext-sme.c",
                type="bugzilla",
            ),
            ErratumReference(
                href="https://bugzilla.redhat.com/show_bug.cgi?id=1773519",
                id="1773519",
                title="CVE-2019-14901 kernel: heap overflow in marvell/mwifiex/tdls.c",
                type="bugzilla",
            ),
            ErratumReference(
                href="https://bugzilla.redhat.com/show_bug.cgi?id=1774671",
                id="1774671",
                title="CVE-2019-14898 kernel: incomplete fix  for race condition between mmget_not_zero()/get_task_mm() and core dumping in CVE-2019-11599",
                type="bugzilla",
            ),
            ErratumReference(
                href="https://bugzilla.redhat.com/show_bug.cgi?id=1774870",
                id="1774870",
                title="CVE-2019-14895 kernel: heap-based buffer overflow in mwifiex_process_country_ie() function in drivers/net/wireless/marvell/mwifiex/sta_ioctl.c",
                type="bugzilla",
            ),
            ErratumReference(
                href="https://www.redhat.com/security/data/cve/CVE-2019-13734.html",
                id="CVE-2019-13734",
                title="CVE-2019-13734",
                type="cve",
            ),
            ErratumReference(
                href="https://www.redhat.com/security/data/cve/CVE-2019-14816.html",
                id="CVE-2019-14816",
                title="CVE-2019-14816",
                type="cve",
            ),
            ErratumReference(
                href="https://www.redhat.com/security/data/cve/CVE-2019-14895.html",
                id="CVE-2019-14895",
                title="CVE-2019-14895",
                type="cve",
            ),
            ErratumReference(
                href="https://www.redhat.com/security/data/cve/CVE-2019-14898.html",
                id="CVE-2019-14898",
                title="CVE-2019-14898",
                type="cve",
            ),
            ErratumReference(
                href="https://www.redhat.com/security/data/cve/CVE-2019-14901.html",
                id="CVE-2019-14901",
                title="CVE-2019-14901",
                type="cve",
            ),
            ErratumReference(
                href="https://www.redhat.com/security/data/cve/CVE-2019-17133.html",
                id="CVE-2019-17133",
                title="CVE-2019-17133",
                type="cve",
            ),
            ErratumReference(
                href="https://access.redhat.com/errata/RHSA-2020:0374",
                id="ref_0",
                title="other_reference_0",
                type="other",
            ),
            ErratumReference(
                href="https://access.redhat.com/containers/?tab=images#/registry.access.redhat.com/devtools/rust-toolset-rhel7",
                id="ref_1",
                title="other_reference_1",
                type="other",
            ),
        ],
    )


def test_errata_url_with_path(fake_errata_tool):
    """Test fetching an advisory when the given ET URL has a path component."""

    source = Source.get(
        "errata:https://errata.example.com/foo/bar?errata=RHBA-2020:0518"
    )

    # It should not have tried to access ET yet (lazy fetching)
    assert not fake_errata_tool.last_url

    # Load all items
    with source:
        items = list(source)

    # It should have queried the expected XML-RPC endpoint, which was
    # appended to the URL retaining our path component.
    # Note that our https was replaced with http, this is expected!
    assert (
        fake_errata_tool.last_url
        == "http://errata.example.com/foo/bar/errata/errata_service"
    )

    # It should have got some data
    assert items
