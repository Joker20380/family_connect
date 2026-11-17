import hashlib
import json
import plistlib
import re
from pathlib import Path


def generate(root: Path, output: Path, native: Path, notices: Path, *,
             bundle='org.familyconnect.mesh.lab', team=None, app_profile=None, tunnel_profile=None):
    if not re.fullmatch(r'[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+){2,}', bundle) or bundle.startswith('com.apple.'):
        raise ValueError('Invalid app-specific bundle identifier')
    if team is not None and not re.fullmatch(r'[A-Z0-9]{10}', team):
        raise ValueError('Team must be a ten-character identifier')
    if bool(team) != bool(app_profile and tunnel_profile):
        raise ValueError('Development signing requires Team and both local profile UUIDs')
    for profile in (app_profile, tunnel_profile):
        if profile is not None and not re.fullmatch(r'[A-Fa-f0-9-]{36}', profile):
            raise ValueError('Provisioning profile must be a UUID, not a file or secret')
    service = bundle + '.materials'
    group_name = '$(AppIdentifierPrefix)' + service
    objects = {}

    def add(key, kind, **fields):
        identifier = hashlib.sha256(key.encode()).hexdigest()[:24].upper()
        objects[identifier] = dict(isa=kind, **fields)
        return identifier

    def reference(path, kind='sourcecode.swift', tree='<absolute>'):
        return add(str(path), 'PBXFileReference', path=str(path), sourceTree=tree, lastKnownFileType=kind)

    def buildfile(name, reference_id, **fields):
        return add(name, 'PBXBuildFile', fileRef=reference_id, **fields)

    shared = [reference(root / 'Shared' / name) for name in ('PacketBridge.swift', 'MaterialStore.swift', 'ProviderLifecycle.swift')]
    app_files = [reference(root / 'App' / name) for name in ('FamilyConnectApp.swift', 'SelfTests.swift', 'VPNController.swift', 'DevelopmentTests.swift')]
    extension_files = [reference(root / 'Extension/PacketTunnelProvider.swift')]
    resource = reference(notices, 'folder')
    products = [reference('FamilyConnect.app', 'wrapper.application', 'BUILT_PRODUCTS_DIR'),
                reference('MeshPacketTunnel.appex', 'wrapper.app-extension', 'BUILT_PRODUCTS_DIR')]
    product_group = add('products', 'PBXGroup', children=products, sourceTree='<group>', name='Products')
    group = add('root', 'PBXGroup', children=shared+app_files+extension_files+[resource, product_group], sourceTree='<group>')
    targets = []
    for index, name in enumerate(('MeshPacketTunnel', 'FamilyConnect')):
        is_extension = index == 0
        files = extension_files if is_extension else app_files
        sources = add(name+'sources', 'PBXSourcesBuildPhase', buildActionMask=2147483647,
                      files=[buildfile(name+item, item) for item in shared+files], runOnlyForDeploymentPostprocessing=0)
        resources = add(name+'resources', 'PBXResourcesBuildPhase', buildActionMask=2147483647,
                        files=[buildfile(name+'notices', resource)], runOnlyForDeploymentPostprocessing=0)
        info = dict(CFBundleIdentifier='$(PRODUCT_BUNDLE_IDENTIFIER)', CFBundleName=name,
                    CFBundleExecutable='$(EXECUTABLE_NAME)', CFBundlePackageType='XPC!' if is_extension else 'APPL',
                    CFBundleShortVersionString='0.0.1', CFBundleVersion='2',
                    FCKeychainGroup=group_name, FCMaterialService=service, FCTunnelBundleID=bundle+'.tunnel')
        if is_extension:
            info['NSExtension'] = dict(NSExtensionPointIdentifier='com.apple.networkextension.packet-tunnel',
                                      NSExtensionPrincipalClass='$(PRODUCT_MODULE_NAME).PacketTunnelProvider')
        else:
            info.update(UILaunchScreen={}, LSRequiresIPhoneOS=True)
        plist = output / (name+'.plist')
        plist.write_bytes(plistlib.dumps(info))
        entitlements = output / (name+'.entitlements')
        entitlements.write_bytes(plistlib.dumps({'com.apple.developer.networking.networkextension': ['packet-tunnel-provider'],
                                               'keychain-access-groups': [group_name]}))
        settings = dict(PRODUCT_NAME=name, PRODUCT_BUNDLE_IDENTIFIER=bundle+('.tunnel' if is_extension else ''),
                        INFOPLIST_FILE=str(plist), CODE_SIGN_ENTITLEMENTS=str(entitlements), SWIFT_VERSION='5.0',
                        IPHONEOS_DEPLOYMENT_TARGET='16.0', TARGETED_DEVICE_FAMILY='1,2',
                        SWIFT_OBJC_BRIDGING_HEADER=str(root / 'Shared/Bridge.h'),
                        LIBRARY_SEARCH_PATHS=[str(native)],
                        OTHER_LDFLAGS=['-lFamilyMesh', '-lresolv', '-framework', 'Security', '-framework', 'CoreFoundation'],
                        LD_GENERATE_MAP_FILE='YES', LD_MAP_FILE_PATH=str(output / (name+'.map')),
                        CODE_SIGNING_ALLOWED='NO', ENABLE_BITCODE='NO',
                        APPLICATION_EXTENSION_API_ONLY='YES' if is_extension else 'NO',
                        SKIP_INSTALL='YES' if is_extension else 'NO')
        if team:
            settings.update(DEVELOPMENT_TEAM=team, CODE_SIGNING_ALLOWED='YES', CODE_SIGN_STYLE='Manual',
                            CODE_SIGN_IDENTITY='Apple Development',
                            PROVISIONING_PROFILE_SPECIFIER=tunnel_profile if is_extension else app_profile)
        config = add(name+'release', 'XCBuildConfiguration', name='Release', buildSettings=settings)
        configs = add(name+'configs', 'XCConfigurationList', buildConfigurations=[config], defaultConfigurationName='Release', defaultConfigurationIsVisible=0)
        phases = [sources, resources]
        dependencies = []
        if not is_extension:
            embedded = buildfile('embedded-extension', products[1], settings={'ATTRIBUTES': ['RemoveHeadersOnCopy'] + (['CodeSignOnCopy'] if team else [])})
            phases.append(add('embed', 'PBXCopyFilesBuildPhase', buildActionMask=2147483647, files=[embedded],
                              dstPath='', dstSubfolderSpec=13, runOnlyForDeploymentPostprocessing=0))
            dependencies.append(add('extension-dependency', 'PBXTargetDependency', target=targets[0]))
        targets.append(add(name, 'PBXNativeTarget', name=name, productName=name, buildConfigurationList=configs,
                           buildPhases=phases, dependencies=dependencies, buildRules=[],
                           productReference=products[1 if is_extension else 0],
                           productType='com.apple.product-type.app-extension' if is_extension else 'com.apple.product-type.application'))
    config = add('projectrelease', 'XCBuildConfiguration', name='Release', buildSettings={})
    configs = add('projectconfigs', 'XCConfigurationList', buildConfigurations=[config], defaultConfigurationName='Release', defaultConfigurationIsVisible=0)
    project = add('project', 'PBXProject', buildConfigurationList=configs, compatibilityVersion='Xcode 14.0',
                  developmentRegion='en', hasScannedForEncodings=0, knownRegions=['en', 'Base'],
                  mainGroup=group, productRefGroup=product_group, projectDirPath='', projectRoot='', targets=targets)

    def encode(value):
        if isinstance(value, dict):
            return '{\n' + ''.join(f'{json.dumps(key)} = {encode(item)};\n' for key, item in value.items()) + '}'
        if isinstance(value, list):
            return '(' + ','.join(encode(item) for item in value) + ')'
        return json.dumps(value)

    path = output / 'FamilyConnect.xcodeproj'
    path.mkdir()
    (path / 'project.pbxproj').write_text(encode(dict(archiveVersion=1, classes={}, objectVersion=56, objects=objects, rootObject=project)))
    return path
