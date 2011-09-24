%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:           cloud-init
Version:        0.6.2
Release:        0.1.bzr457%{?dist}
Summary:        Cloud instance init scripts

Group:          System Environment/Base
License:        GPLv3
URL:            http://launchpad.net/cloud-init
# bzr export -r 457 cloud-init-0.6.2-bzr457.tar.gz lp:cloud-init
Source0:        %{name}-%{version}-bzr457.tar.gz
Source1:        cloud-init-fedora.cfg
Source2:        cloud-init-README.fedora
Patch0:         cloud-init-0.6.2-fedora.patch

# The current patch set is in flux as we stabilize cloud-init on Fedora.
# It will be submitted upstream as soon as it becomes reasonable to do so.

# Add systemd support (not yet upstream)
Patch2:         cloud-init-0.6.2-systemd.patch
# Restore SSH files' selinux contexts (not yet upstream)
Patch3:         cloud-init-0.6.2-sshcontext.patch
# Make locale file location configurable (not yet upstream)
Patch4:         cloud-init-0.6.2-localefile.patch
# Write timezone data to /etc/sysconfig/clock (not yet upstream)
Patch5:         cloud-init-0.6.2-tzsysconfig.patch
# Restore puppet files' selinux contexts (not yet upstream)
Patch6:         cloud-init-0.6.2-puppetcontext.patch
# Make enabling the puppet service work on Fedora (not yet upstream)
Patch7:         cloud-init-0.6.2-puppetenable.patch
# Make the types of SSH keys to generate configurable (not yet upstream)
Patch8:         cloud-init-0.6.2-sshkeytypes.patch
# https://bugs.launchpad.net/cloud-init/+bug/857926
Patch10:        cloud-init-0.6.2-runparts-emptydir.patch

BuildArch:      noarch
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires:  python-devel
BuildRequires:  python-setuptools-devel
BuildRequires:  systemd-units
Requires:       e2fsprogs
Requires:       iproute
Requires:       libselinux-python
Requires:       net-tools
Requires:       procps
Requires:       python-boto
Requires:       python-cheetah
Requires:       python-configobj
Requires:       PyYAML
Requires:       rsyslog
Requires:       shadow-utils
Requires:       xfsprogs
Requires:       /usr/bin/run-parts
Requires(post):   systemd-units
Requires(preun):  systemd-units
Requires(postun): systemd-units

%description
Cloud-init is a set of init scripts for cloud instances.  Cloud instances
need special scripts to run during initialization to retrieve and install
ssh keys and to let the user run various scripts.


%prep
%setup -q -n %{name}-%{version}-bzr457
%patch0 -p1
%patch2 -p1
%patch3 -p1
%patch4 -p1
%patch5 -p1
%patch6 -p1
%patch7 -p1
%patch8 -p1
%patch10 -p1

cp -p %{SOURCE2} README.fedora


%build
%{__python} setup.py build


%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

for x in $RPM_BUILD_ROOT/%{_bindir}/*.py; do mv "$x" "${x%.py}"; done
chmod +x $RPM_BUILD_ROOT/%{python_sitelib}/cloudinit/SshUtil.py
mkdir -p $RPM_BUILD_ROOT/%{_sharedstatedir}/cloud

# We supply our own config file since our software differs from Ubuntu's.
cp -p %{SOURCE1} $RPM_BUILD_ROOT/%{_sysconfdir}/cloud/cloud.cfg

# Note that /etc/rsyslog.d didn't exist by default until F15.
# el6 request: https://bugzilla.redhat.com/show_bug.cgi?id=740420
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/rsyslog.d
cp -p tools/21-cloudinit.conf $RPM_BUILD_ROOT/%{_sysconfdir}/rsyslog.d/21-cloudinit.conf

# Install the systemd bits
mkdir -p        $RPM_BUILD_ROOT/%{_unitdir}
cp -p systemd/* $RPM_BUILD_ROOT/%{_unitdir}


%clean
rm -rf $RPM_BUILD_ROOT


%post
if [ $1 -eq 1 ] ; then
    # Initial installation
    # Enabled by default per "runs once then goes away" exception
    /bin/systemctl enable cloud-config.service     >/dev/null 2>&1 || :
    /bin/systemctl enable cloud-final.service      >/dev/null 2>&1 || :
    /bin/systemctl enable cloud-init.service       >/dev/null 2>&1 || :
    /bin/systemctl enable cloud-init-local.service >/dev/null 2>&1 || :
fi

%preun
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    /bin/systemctl --no-reload disable cloud-config.service >/dev/null 2>&1 || :
    /bin/systemctl --no-reload disable cloud-final.service  >/dev/null 2>&1 || :
    /bin/systemctl --no-reload disable cloud-init.service   >/dev/null 2>&1 || :
    /bin/systemctl --no-reload disable cloud-init-local.service >/dev/null 2>&1 || :
    # One-shot services -> no need to stop
fi

%postun
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
# One-shot services -> no need to restart


%files
%doc ChangeLog LICENSE TODO README.fedora
%config(noreplace) %{_sysconfdir}/cloud/cloud.cfg
%dir               %{_sysconfdir}/cloud/cloud.cfg.d
%config(noreplace) %{_sysconfdir}/cloud/cloud.cfg.d/*.cfg
%doc               %{_sysconfdir}/cloud/cloud.cfg.d/README
%dir               %{_sysconfdir}/cloud/templates
%config(noreplace) %{_sysconfdir}/cloud/templates/*
%{_unitdir}/cloud-config.service
%{_unitdir}/cloud-config.target
%{_unitdir}/cloud-final.service
%{_unitdir}/cloud-init-local.service
%{_unitdir}/cloud-init.service
%{python_sitelib}/*
%{_libexecdir}/%{name}
%{_bindir}/cloud-init*
%doc %{_datadir}/doc/%{name}
%dir %{_sharedstatedir}/cloud

%config(noreplace) %{_sysconfdir}/rsyslog.d/21-cloudinit.conf


%changelog
* Sat Sep 24 2011 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.2-0.1.bzr457
- Rebased against upstream rev 457
- Added missing dependencies

* Fri Sep 23 2011 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.2-0.4.bzr450
- Added more macros to the spec file

* Fri Sep 23 2011 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.2-0.3.bzr450
- Fixed logfile permission checking
- Fixed SSH key generation
- Fixed a bad method call in FQDN-guessing [LP:857891]
- Updated localefile patch
- Disabled the grub_dpkg module
- Fixed failures due to empty script dirs [LP:857926]

* Fri Sep 23 2011 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.2-0.2.bzr450
- Updated tzsysconfig patch

* Wed Sep 21 2011 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.2-0.1.bzr450
- Initial packaging
