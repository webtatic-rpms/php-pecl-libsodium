# Fedora repo spec file for php-pecl-libsodium
# with SCL compatibility removed, from
#
# remirepo spec file for php-pecl-libsodium
#
# Copyright (c) 2014-2015 Remi Collet
# License: CC-BY-SA
# http://creativecommons.org/licenses/by-sa/4.0/
#
# Please, preserve the changelog entries
#
%{!?php_inidir:  %global php_inidir  %{_sysconfdir}/php.d}
%{!?__pecl:      %global __pecl      %{_bindir}/pecl}
%{!?__php:       %global __php       %{_bindir}/php}

%global with_zts   0%{?__ztsphp:1}
%global basepkg   %{?basepkg}%{!?basepkg:php}
%global pecl_name  libsodium
%global with_tests 0%{!?_without_tests:1}
%if "%{php_version}" < "5.6"
%global ini_name   %{pecl_name}.ini
%else
%global ini_name   40-%{pecl_name}.ini
%endif
%global buildver   %(pkg-config --silence-errors --modversion libsodium 2>/dev/null || echo 65536)

Summary:        Wrapper for the Sodium cryptographic library
Name:           %{basepkg}-pecl-%{pecl_name}
Version:        1.0.6
Release:        1.2%{?dist}
License:        BSD
Group:          Development/Languages
URL:            http://pecl.php.net/package/%{pecl_name}
Source0:        http://pecl.php.net/get/%{pecl_name}-%{version}.tgz

BuildRequires:  libsodium-devel >= 0.6.0
BuildRequires:  %{basepkg}-devel > 5.2
BuildRequires:  %{basepkg}-pear
BuildRequires:  %{basepkg}-json
BuildRequires:  pkgconfig

Requires:       php(zend-abi) = %{php_zend_api}
Requires:       php(api) = %{php_core_api}
Requires:       libsodium%{?_isa} >= %{buildver}

Provides:       php-%{pecl_name} = %{version}
Provides:       php-%{pecl_name}%{?_isa} = %{version}
Provides:       php-pecl(%{pecl_name}) = %{version}
Provides:       php-pecl(%{pecl_name})%{?_isa} = %{version}

# Filter shared private - always as libsodium.so is a bad name
%{?filter_provides_in: %filter_provides_in %{_libdir}/.*\.so$}
%{?filter_setup}


%description
A simple, low-level PHP extension for libsodium.

Documentation: https://paragonie.com/book/pecl-libsodium


%prep
%setup -q -c
mv %{pecl_name}-%{version} NTS

# Don't install tests
sed -e '/role="test"/d' -i package.xml

cd NTS

# Sanity check, really often broken
extver=$(sed -n '/#define PHP_LIBSODIUM_VERSION/{s/.* "//;s/".*$//;p}' php_libsodium.h)
if test "x${extver}" != "x%{version}"; then
   : Error: Upstream extension version is ${extver}, expecting %{version}.
   exit 1
fi
cd ..

%if %{with_zts}
# Duplicate source tree for NTS / ZTS build
cp -pr NTS ZTS
%endif

# Create configuration file
cat > %{ini_name} << 'EOF'
; Enable %{pecl_name} extension module
extension=%{pecl_name}.so
EOF


%build
cd NTS
%{_bindir}/phpize
%configure \
    --with-php-config=%{_bindir}/php-config
make %{?_smp_mflags}

%if %{with_zts}
cd ../ZTS
%{_bindir}/zts-phpize
%configure \
    --with-php-config=%{_bindir}/zts-php-config
make %{?_smp_mflags}
%endif


%install
make -C NTS install INSTALL_ROOT=%{buildroot}

# install config file
install -D -m 644 %{ini_name} %{buildroot}%{php_inidir}/%{ini_name}

# Install XML package description
install -D -m 644 package.xml %{buildroot}%{pecl_xmldir}/%{pecl_name}.xml

%if %{with_zts}
make -C ZTS install INSTALL_ROOT=%{buildroot}

install -D -m 644 %{ini_name} %{buildroot}%{php_ztsinidir}/%{ini_name}
%endif

# Documentation
for i in $(grep 'role="doc"' package.xml | sed -e 's/^.*name="//;s/".*$//')
do install -Dpm 644 NTS/$i %{buildroot}%{pecl_docdir}/%{pecl_name}/$i
done


# when pear installed alone, after us
%triggerin -- %{basepkg}-pear
if [ -x %{__pecl} ] ; then
    %{pecl_install} %{pecl_xmldir}/%{pecl_name}.xml >/dev/null || :
fi

# posttrans as pear can be installed after us
%posttrans
if [ -x %{__pecl} ] ; then
    %{pecl_install} %{pecl_xmldir}/%{pecl_name}.xml >/dev/null || :
fi

%postun
if [ $1 -eq 0 -a -x %{__pecl} ] ; then
    %{pecl_uninstall} %{pecl_name} >/dev/null || :
fi


%check
cd NTS
: Minimal load test for NTS extension
%{__php} --no-php-ini \
    --define extension=%{buildroot}%{php_extdir}/%{pecl_name}.so \
    --modules | grep %{pecl_name}

%if %{with_tests}
: Upstream test suite  for NTS extension
TEST_PHP_EXECUTABLE=%{__php} \
TEST_PHP_ARGS="-n -d extension=json.so -d extension=$PWD/modules/%{pecl_name}.so" \
NO_INTERACTION=1 \
REPORT_EXIT_STATUS=1 \
%{__php} -n run-tests.php --show-diff
%endif

%if %{with_zts}
cd ../ZTS
: Minimal load test for ZTS extension
%{__ztsphp} --no-php-ini \
    --define extension=%{buildroot}%{php_ztsextdir}/%{pecl_name}.so \
    --modules | grep %{pecl_name}

%if %{with_tests}
: Upstream test suite  for ZTS extension
TEST_PHP_EXECUTABLE=%{_bindir}/zts-php \
TEST_PHP_ARGS="-n -d extension=json.so -d extension=$PWD/modules/%{pecl_name}.so" \
NO_INTERACTION=1 \
REPORT_EXIT_STATUS=1 \
%{_bindir}/zts-php -n run-tests.php --show-diff
%endif
%endif


%files
%doc %{pecl_docdir}/%{pecl_name}
%{?_licensedir:%license NTS/LICENSE}
%{pecl_xmldir}/%{pecl_name}.xml

%config(noreplace) %{php_inidir}/%{ini_name}
%{php_extdir}/%{pecl_name}.so

%if %{with_zts}
%config(noreplace) %{php_ztsinidir}/%{ini_name}
%{php_ztsextdir}/%{pecl_name}.so
%endif


%changelog
* Sun Jan 14 2018 Andy Thompson <andy@webtatic.com> - 1.0.6-1.2
- Rebuild for php-7.2.0 Zend ABI version change

* Sat Jun 24 2017 Andy Thompson <andy@webtatic.com> - 1.0.6-1.1
- Rebuild for php-7.2.0alpha2 Zend ABI version change

* Sun Jun 11 2017 Andy Thompson <andy@webtatic.com> - 1.0.6-1
- fork from EPEL php-pecl-libsodium-1.0.2-1
- update to 1.0.6
- remove pr70 patch released upstream