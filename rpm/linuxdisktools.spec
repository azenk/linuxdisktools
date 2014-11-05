Name:		linuxdisktools
Version:	1.0
Release:	1%{?dist}
Summary:	Useful tools for storage management in linux

Group:		
License:	
URL:		https://github.com/chuckleb/linuxdisktools
Source0:	linuxdisktools.tgz
BuildRoot:	%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

BuildRequires:	
Requires:	MegaCli

%description


%prep
%setup -q


%build


%install
rm -rf %{buildroot}
install LSI/lsitools.sh %{buildroot}/usr/local/sbin/


%clean
rm -rf %{buildroot}


%files
%defattr(-,root,root,-)
%doc
/usr/local/sbin/lsitools.sh



%changelog

