#!/usr/bin/python3

from debian import debian_support
import oras.provider
import hashlib
import os

oci_repo = os.environ.get("OCI_REPO")
oci_auth_name = os.environ.get("OCI_AUTH_NAME")

def calculate_sha256(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def read_repo_file(repo_file):
    all_pkg_infos = []
    file_sha256_info_list = []
    for pkg_info in list(repo_file):
        pkg_metainfo = {}
        for tag_value in pkg_info:
            pkg_metainfo[tag_value[0]] = tag_value[1]
        all_pkg_infos.append(pkg_metainfo)
    if "Filename" in all_pkg_infos[0]:
        for all_pkg_info in all_pkg_infos:
            file_sha256_info = {}
            file_sha256_info["Filename"] = all_pkg_info["Filename"].strip("./")
            file_sha256_info["SHA256"] = all_pkg_info["SHA256"]
            file_sha256_info_list.append(file_sha256_info)
    elif "Checksums-Sha256" in all_pkg_infos[0]:
        for all_pkg_info in all_pkg_infos:
            for sha256_info in all_pkg_info["Checksums-Sha256"].split("\n"):
                if sha256_info == "":
                    continue
                file_sha256_info = {}
                file_sha256_info["Filename"] = sha256_info.split(" ")[2]
                file_sha256_info["SHA256"] = sha256_info.split(" ")[0]
                file_sha256_info_list.append(file_sha256_info)
    else:
        return {}
    return  file_sha256_info_list

def upload_blobs_manifest(blob_file_name, blob_file_digest, oci_repo):
    token = os.environ.get("GH_TK")
    class MyProvider(oras.provider.Registry):
        pass

    reg = MyProvider()
    container = reg.get_container(oci_repo)
    manifest = reg.get_manifest(container)

    blob = os.path.join(os.getcwd(), blob_file_name)
    blob_name = os.path.basename(blob)
    annotset = oras.oci.Annotations({})
    layer = oras.oci.NewLayer(blob, "application/octet-stream", is_dir=False)
    layer["annotations"] = {oras.defaults.annotation_title: blob_name}
    reg.set_basic_auth(oci_auth_name, token)
    print("going to upload blob %s" % blob)
    print(reg.upload_blob(blob, container, layer))

    new_layers = []
    for old_layer in manifest["layers"]:
        if  old_layer["annotations"][oras.defaults.annotation_title] == blob_file_name:
            print("going to delete old %s layer %s" % (blob_file_name, old_layer))
        else:
            if old_layer["annotations"] == {oras.defaults.annotation_title: blob_name} and old_layer["digest"] != "sha256:" + blob_file_digest:
                print("going to delete conflict layer %s" % old_layer)
            else:
                new_layers.append(old_layer)

    manifest["layers"] = new_layers
    manifest["layers"].append(layer)
    print("going to upload manifest")
    print(reg.upload_manifest(manifest, container))

def delete_blobs_manifest(blob_file_name, blob_file_digest, oci_repo):
    token = os.environ.get("GH_TK")
    class MyProvider(oras.provider.Registry):
        pass

    reg = MyProvider()
    container = reg.get_container(oci_repo)
    manifest = reg.get_manifest(container)
    new_layers = []
    delete_layer = False
    for old_layer in manifest["layers"]:
        if blob_file_name == old_layer["annotations"][oras.defaults.annotation_title]:
            delete_layer = True
    for old_layer in manifest["layers"]:
        if delete_layer:
            if blob_file_name == old_layer["annotations"][oras.defaults.annotation_title]:
                print("%s exist in remote, going to delete" % blob_file_name)
            else:
                new_layers.append(old_layer)
    manifest["layers"] = new_layers
    print("going to upload manifest")
    reg.set_basic_auth(oci_auth_name, token)
    print(reg.upload_manifest(manifest, container))


# Get manifest from remote repo
class MyProvider(oras.provider.Registry):
    pass

reg = MyProvider()
container = reg.get_container(oci_repo)
manifest = reg.get_manifest(container)

# Get remote package file name and digest info from manifest
remote_file_sha256_infos =  []
remote_extra_file_sha256_infos =  []
for oci_layer in manifest["layers"]:
    remote_file_sha256_info = {}
    remote_file_sha256_info["Filename"] = oci_layer["annotations"]["org.opencontainers.image.title"]
    remote_file_sha256_info["SHA256"] = oci_layer["digest"].split(":")[1]
    if oci_layer["annotations"]["org.opencontainers.image.title"] == "Packages" or oci_layer["annotations"]["org.opencontainers.image.title"] == "Sources":
        remote_extra_file_sha256_infos.append(remote_file_sha256_info)
    else:
        remote_file_sha256_infos.append(remote_file_sha256_info)

# Read info of packages to upload from local Packages and Sources
pkg_file = debian_support.PackageFile("Packages")
source_file = debian_support.PackageFile("Sources")
package_info_list = read_repo_file(pkg_file)
source_info_list = read_repo_file(source_file)
all_package_list = package_info_list + source_info_list

# Skip packages already exist in remote repo
new_package_list = []
for package_info in all_package_list:
    remote_exist = False
    hash_match = False
    for remote_file_sha256_info in remote_file_sha256_infos:
        if package_info["Filename"] == remote_file_sha256_info["Filename"]:
            remote_exist = True
            if package_info["SHA256"] == remote_file_sha256_info["SHA256"]:
                hash_match = True
    if not (remote_exist and hash_match):
        new_package_list.append(package_info)

# Find deleted packages
package_list_to_delete = []
for remote_file_package_info in remote_file_sha256_infos:
    local_exist = False
    for local_package_info in all_package_list:
        if remote_file_package_info["Filename"] == local_package_info["Filename"]:
            local_exist = True
    if not local_exist:
        package_list_to_delete.append(remote_file_package_info)

# Always upload Packages and Sources file
for extra_file in ["Packages", "Sources"]:
    extra_file_info = {}
    extra_file_info["Filename"] = extra_file
    extra_file_info["SHA256"] = calculate_sha256(os.path.join(os.getcwd(), extra_file))
    extra_remote_exist = False
    extra_hash_match = False
    for extra_file_remote_info in remote_extra_file_sha256_infos:
        if extra_file_info["Filename"] == extra_file_remote_info["Filename"]:
            extra_remote_exist = True
            if extra_file_info["SHA256"] == extra_file_remote_info["SHA256"]:
                extra_hash_match = True
    if not (extra_remote_exist and extra_hash_match):
        new_package_list.append(extra_file_info)

# Upload packages one by one
for upload_file_info in new_package_list:
    upload_blobs_manifest(upload_file_info["Filename"], upload_file_info["SHA256"], oci_repo)

# Delete useless packages
for delete_package_info in package_list_to_delete:
    delete_blobs_manifest(delete_package_info["Filename"], delete_package_info["SHA256"], oci_repo)
