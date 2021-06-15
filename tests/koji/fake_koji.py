import os


class FakeKojiController(object):
    def __init__(self):
        self.rpm_data = {}
        self.build_data = {}
        self.archive_data = {}
        self.last_url = None
        self.next_build_id = 80000

    def reset(self):
        self.rpm_data = {}
        self.build_data = {}
        self.archive_data = {}
        self.last_url = None
        self.next_build_id = 80000

    def session(self, url):
        self.last_url = url
        return FakeKojiSession(self)

    def ensure_build(self, build_nvr):
        if build_nvr in self.build_data:
            return self.build_data[build_nvr]

        # Have to make a new build
        build_id = self.next_build_id
        self.next_build_id += 1

        build_data = {"id": build_id}
        build_data["nvr"] = build_nvr
        r, v, n = build_nvr[-1::-1].split("-", 2)
        build_data["name"] = n[-1::-1]
        build_data["version"] = v[-1::-1]
        build_data["release"] = r[-1::-1]

        self.build_data[build_id] = build_data
        self.build_data[build_data["nvr"]] = build_data

        return build_data

    def insert_rpms(self, filenames, koji_dir=None, signing_key=None, build_nvr=None):

        stored_rpms = []

        for filename in filenames:
            data = {}
            rfilename = filename[-1::-1]
            (rpm, arch, rest) = rfilename.split(".", 2)
            rpm = rpm[-1::-1]
            assert rpm == "rpm"
            data["arch"] = arch[-1::-1]

            (r, v, n) = rest.split("-", 2)
            data["name"] = n[-1::-1]
            data["version"] = v[-1::-1]
            data["release"] = r[-1::-1]
            stored_rpms.append(data)

            if not build_nvr and data["arch"] == "src":
                build_nvr = "%s-%s-%s" % (
                    data["name"],
                    data["version"],
                    data["release"],
                )

            self.rpm_data[filename] = data

        # If build_nvr wasn't passed to us already, it should be set by now.
        # Ensure build exists and reference it from all the new RPMs.
        build_data = self.ensure_build(build_nvr)
        for rpm in stored_rpms:
            rpm["build_id"] = build_data["id"]

        if koji_dir and signing_key:
            # Make signed RPMs exist
            for filename in filenames:
                signed_rpm_path = os.path.join(
                    koji_dir,
                    "packages/{build[name]}/{build[version]}/{build[release]}",
                    "data/signed/{signing_key}/{rpm[arch]}/{filename}",
                ).format(
                    build=build_data,
                    rpm=self.rpm_data[filename],
                    filename=filename,
                    signing_key=signing_key,
                )

                signed_dir = os.path.dirname(signed_rpm_path)
                if not os.path.exists(signed_dir):
                    os.makedirs(signed_dir)
                open(signed_rpm_path, "w")

    def insert_archives(self, archives, build_nvr):
        build = self.ensure_build(build_nvr)
        self.archive_data[build["id"]] = archives
        self.archive_data[build["nvr"]] = archives

    def insert_modules(self, filenames, build_nvr):
        archives = [
            {"btype": "module", "filename": filename, "nvr": build_nvr}
            for filename in filenames
        ]
        self.insert_archives(archives, build_nvr)


class FakeKojiSession(object):
    def __init__(self, controller):
        self._ctrl = controller

    def _return_or_raise(self, value):
        if isinstance(value, Exception):
            raise value
        return value

    def getRPM(self, rpm):
        return self._return_or_raise(self._ctrl.rpm_data.get(rpm))

    def getBuild(self, build_id):
        return self._return_or_raise(self._ctrl.build_data.get(build_id))

    def listArchives(self, build_id):
        return self._return_or_raise(self._ctrl.archive_data.get(build_id) or [])

    def multicall(self, *args, **kwargs):
        return FakeMulticall(self, *args, **kwargs)


class PendingCall(object):
    def __init__(self, result):
        self._result = result
        self._done = False

    @property
    def result(self):
        if not self._done:
            raise RuntimeError("Called .result on multicall before done")
        return self._result


class FakeMulticall(object):
    def __init__(self, session, strict=None, batch=None):
        self._pending = []
        self.getRPM = self._proxy(session.getRPM)
        self.getBuild = self._proxy(session.getBuild)
        self.listArchives = self._proxy(session.listArchives)

    def call_all(self, strict=None, batch=None):
        for call in self._pending:
            call._done = True

    def _proxy(self, session_fn):
        def new_fn(*args, **kwargs):
            out = PendingCall(session_fn(*args, **kwargs))
            self._pending.append(out)
            return out

        return new_fn
