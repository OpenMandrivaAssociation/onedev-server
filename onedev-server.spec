%undefine _debugsource_packages

%global __java_requires %{nil}
%global __java_provides %{nil}
%global __jmod_requires %{nil}
%global __jmod_provides %{nil}
%global __osgi_requires %{nil}
%global __osgi_provides %{nil}

%global rootpath /srv/%{name}
%global bootpath %{rootpath}/boot
%global confpath %{rootpath}/conf
%global dbpath %{rootpath}/db
%global libpath %{rootpath}/lib
%global sitepath %{rootpath}/site
%global temppath %{rootpath}/temp

Name:      onedev-server
Version:   14.0.7
Release:   2
Summary:   The powerful and simple DevOps platform
URL:       https://code.onedev.io/onedev/server
License:   MIT
Group:     Servers

# List of available releases:
# https://code.onedev.io/onedev/server/~builds?query=%22Job%22+is+%22Release%22+and+successful
# https://code.onedev.io/~downloads/projects/160/archives?revision=refs/tags/v14.0.7&format=tgz
Source0:   %{name}-%{version}.tar.gz
Source1:   %{name}-%{version}-deps.tar.zst
Source10:  %{name}.sysusers
Source20:  logback.xml
Source30:  tanuki-wrapper.conf

Patch0:  ee-build-fix.patch

Obsoletes:  onedev

BuildRequires:  jdk-current
BuildRequires:  maven >= 3.8.1
BuildRequires:  tanuki-wrapper
BuildRequires:  unzip

Requires:  curl
Requires:  git
Requires:  git-lfs
Requires:  tanuki-wrapper
# https://code.onedev.io/onedev/server/~issues/903
Requires:  fontconfig
Requires:  fonts-ttf-dejavu

%description
Git server with CI/CD, kanban, and packages.
Seamless integration. Unparalleled experience.

%prep
%autosetup -a 1 -p 1 -c

%build
%{_datadir}/maven/bin/mvn -Dmaven.repo.local=repository \
    -DskipTests \
    package

%install
mkdir -p %{buildroot}%{bootpath} \
         %{buildroot}%{confpath} \
         %{buildroot}%{dbpath} \
         %{buildroot}%{temppath}

unzip server-product/target/onedev-%{version}.zip
mv onedev-%{version}/* .

# User
mkdir -p %{buildroot}%{_sysusersdir}
cp %{S:10} %{buildroot}%{_sysusersdir}/%{name}.conf

# Config
mv release.properties %{buildroot}%{rootpath}/
sed -i 's|\${installDir}/internaldb|\${installDir}/db|g' conf/hibernate.properties
mv conf/*.properties %{buildroot}%{confpath}/
cp %{S:20} %{buildroot}%{confpath}/
cp %{S:30} %{buildroot}%{confpath}/

# Incompatibilities tracker
mv incompatibilities %{buildroot}%{rootpath}/

# Files, including repositories, are stored here
mv site %{buildroot}%{sitepath}

# JARs
rm boot/wrapper.jar
mv boot/*.jar %{buildroot}%{bootpath}/
mv lib %{buildroot}/%{libpath}

# A random UUID is written into this test file to check permissions
touch %{buildroot}%{rootpath}/test

# Fix images basepath in readme
sed -i 's#](./doc/images/#](images/#' readme.md

# Systemd integration
. /etc/profile.d/90java.sh

mkdir -p %{buildroot}%{_unitdir}
cat >%{buildroot}%{_unitdir}/%{name}.service <<EOF
[Unit]
Description=%{summary}
After=syslog.target network-online.target

[Service]
Type=simple
User=%{name}
Group=%{name}
ExecStart=tanuki-wrapper %{confpath}/tanuki-wrapper.conf \
wrapper.pidfile="%{_rundir}/%{name}/tanuki-wrapper.pid"
RuntimeDirectory=%{name}
RuntimeDirectoryMode=0700
Environment=JAVA_HOME=$JAVA_HOME

[Install]
WantedBy=multi-user.target
EOF

%pretrans
# onedev -> onedev-server migration
if getent passwd onedev >/dev/null && ! getent passwd %{name} >/dev/null; then
	echo "Renaming system user onedev → %{name}"
	usermod -l %{name} onedev
	groupmod -n %{name} onedev || true

	if [ -d /srv/onedev ]; then
		mv /srv/onedev /srv/%{name}
		usermod -d /srv/%{name} %{name}
	fi
fi

%files
%doc doc/images
%doc readme.md
%license license.txt
%{_sysusersdir}/%{name}.conf
%{_unitdir}/%{name}.service

%dir %attr(0755,root,root) %{rootpath}
%dir %attr(0755,root,root) %{bootpath}
%dir %attr(0755,root,root) %{confpath}
%dir %attr(0770,root,%{name}) %{dbpath}
%dir %attr(0755,root,root) %{libpath}
%dir %attr(0770,root,%{name}) %{temppath}
%dir %attr(0770,root,%{name}) %{sitepath}
%dir %attr(0770,root,%{name}) %{sitepath}/assets
%dir %attr(0770,root,%{name}) %{sitepath}/assets/avatars
%dir %attr(0755,root,root) %{rootpath}/incompatibilities
%dir %attr(0755,root,root) %{sitepath}/lib

%attr(0644,root,root) %{rootpath}/release.properties
%config(noreplace) %attr(0640,root,%{name}) %{confpath}/hibernate.properties
%config(noreplace) %attr(0640,root,%{name}) %{confpath}/server.properties
%attr(0644,root,root) %{confpath}/logback.xml
%attr(0644,root,root) %{confpath}/tanuki-wrapper.conf
%attr(0644,root,root) %{bootpath}/*
%attr(0644,root,root) %{libpath}/*
%attr(0640,onedev-server,onedev-server) %{sitepath}/assets/avatars/*
%attr(0644,root,root) %{sitepath}/assets/prefetch.json
%attr(0644,root,root) %{sitepath}/assets/robots.txt
%attr(0644,root,root) %{rootpath}/incompatibilities/*
%attr(0644,root,root) %{sitepath}/lib/*

%attr(0664,root,onedev-server) %{rootpath}/test
