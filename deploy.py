#!/usr/bin/env python3
import logging
import tempfile
import argparse
import time
import boto3
import requests
import gzip
import shutil
import tarfile
import os
import configparser
from pathlib import Path
import glob

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# create formatter and add it to the handlers
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(ch)


def getUrl(tmpdirname: str, url: str):
    local_filename = url.split("/")[-1]

    srcdir = os.path.join(tmpdirname, "source")
    os.mkdir(srcdir)

    srcpackage = os.path.join(srcdir, local_filename)

    logger.info(f"getting file {srcpackage} from {url}")
    response = requests.get(url)
    if response.status_code == 200:
        logger.debug("Response 200")
        with open(srcpackage, "wb") as fd:
            fd.write(response.content)
        return srcpackage
    else:
        logger.error(f"Error {response.status_code}")
        raise FileNotFoundError()


def getSplunkbase(tmpdirname: str, url: str):
    id = url.split("/")[-2]
    ver = url.split("/")[-1]
    local_filename = "app.tgz"
    user = os.environ["SPLUNK_BASE_USER"]
    password = os.environ["SPLUNK_BASE_PASSWORD"]
    creds = {"username": user, "password": password}
    with requests.session() as s:
        auth = s.post(
            "https://splunkbase.splunk.com/api/account:login",
            data=creds
        )    
        if auth.status_code == 200:        
            logger.info("Authenticated to splunkbase")
            root = ET.fromstring(auth.content)
            logger.info(root)
            
        else:
            raise Exception("Invalid user/pass")
        
        srcdir = os.path.join(tmpdirname, "source")
        os.mkdir(srcdir)

        srcpackage = os.path.join(srcdir, local_filename)
        url = f"https://splunkbase.splunk.com/app/{id}/release/{ver}/download?origin=asc&lead=true"
        logger.info(f"getting file {srcpackage} from {url}")
        response = s.get(url)
        if response.status_code == 200:
            logger.debug("Response 200")
            with open(srcpackage, "wb") as fd:
                fd.write(response.content)
            return srcpackage
        else:
            logger.error(f"Error {response.status_code}")
            raise FileNotFoundError()


def cut_cook_config(expanded_app_path, cutpath_app_path, appname, cutoutpath_app_path):
    idxpropsconfig = configparser.ConfigParser()
    idxpropsconfig.optionxform = str
    propsconfig = configparser.ConfigParser()
    propsconfig.optionxform = str
    iscooked = False
    for dir in ["default", "local"]:

        propsconfig.read(os.path.join(expanded_app_path, dir, "props.conf"))
        for s in propsconfig.sections():
            # print(s)
            for c in propsconfig[s]:
                # print(c)
                if c.startswith("FIELDALIAS"):
                    continue
                elif c.startswith("EXTRACT"):
                    continue
                elif c.startswith("REPORT"):
                    continue
                elif c.startswith("EVAL"):
                    continue
                elif c.startswith("FIELDALIAS"):
                    continue
                elif c.startswith("LOOKUP"):
                    continue
                else:
                    if s not in idxpropsconfig.sections():
                        idxpropsconfig[s] = {}
                    idxpropsconfig[s][c] = propsconfig[s][c]
                    iscooked = True
        with open(os.path.join(cutpath_app_path, dir, "props.conf"), "w") as configfile:
            idxpropsconfig.write(configfile)

        idxtransformsconfig = configparser.ConfigParser()
        idxtransformsconfig.optionxform = str
        transformsconfig = configparser.ConfigParser()
        transformsconfig.optionxform = str
        propsconfig.read(os.path.join(expanded_app_path, dir, "transforms.conf"))
        for s in transformsconfig.sections():
            if "filename" in transformsconfig[s]:
                continue
            elif "collection" in transformsconfig[s]:
                continue
            elif "external_type" in transformsconfig[s]:
                continue
            else:
                iscooked = True
                idxtransformsconfig[s] = transformsconfig[s]

        with open(
            os.path.join(cutpath_app_path, dir, "transforms.conf"), "w"
        ) as configfile:
            idxtransformsconfig.write(configfile)

    if iscooked:
        os.mkdir(cutoutpath_app_path)

        with tarfile.open(f"{cutoutpath_app_path}/{appname}.tgz", "w:gz") as tar:
            tar.add(cutpath_app_path, arcname=os.path.basename(appname))

    return iscooked


def main(tmpdirname: str):
    parser = argparse.ArgumentParser(
        description="Control app deployment for app-framework"
    )
    parser.add_argument("--s3endpoint")
    parser.add_argument("--s3bucket")
    parser.add_argument("--s3root")
    parser.add_argument("--cut", action=argparse.BooleanOptionalAction)
    parser.add_argument("--base", action=argparse.BooleanOptionalAction)
    parser.add_argument("--sh", action="append")
    parser.add_argument("--idxc", action="append")
    parser.add_argument("--fwd", action="append")
    parser.add_argument("--ds", action="append")
    parser.add_argument("--source")
    pargs = parser.parse_args()

    if pargs.source.startswith("http"):
        local_filename = getUrl(tmpdirname, pargs.source)
    elif pargs.source.startswith("splunkbase"):
        local_filename = getSplunkbase(tmpdirname, pargs.source)
    expanddir = os.path.join(tmpdirname, "expanded")
    os.mkdir(expanddir)
    logger.info(f"expanding {local_filename} to {expanddir}")
    tar = tarfile.open(local_filename)
    appname = tar.getnames()[0]
    tar.extractall(path=expanddir)
    tar.close()
    logger.info(f"expanded {appname}")

    #
    expanded_app_path = os.path.join(expanddir, appname)
    cutpath_app_path = os.path.join(expanddir, "cut", appname)

    attemptcut = False
    if os.path.exists(os.path.join(expanded_app_path, "default", "props.conf")):
        logger.info("Has default/props.conf")
        attemptcut = True
    if os.path.exists(os.path.join(expanded_app_path, "local", "props.conf")):
        logger.info("Has local/props.conf")
        attemptcut = True

    outputdir = os.path.join(tmpdirname, "output")
    os.mkdir(outputdir)
    if pargs.cut:
        logger.info("Applying cut")
        os.mkdir(os.path.join(expanddir, "cut"))
        os.mkdir(cutpath_app_path)
        os.mkdir(os.path.join(cutpath_app_path, "default"))
        os.mkdir(os.path.join(cutpath_app_path, "local"))

        if os.path.exists(os.path.join(expanded_app_path, "app.manifest")):
            shutil.copy(
                os.path.join(expanded_app_path, "app.manifest"), cutpath_app_path
            )
        if os.path.exists(os.path.join(expanded_app_path, "default", "app.conf")):
            shutil.copy(
                os.path.join(expanded_app_path, "default", "app.conf"),
                os.path.join(cutpath_app_path, "default"),
            )

        cutoutpath_app_path = os.path.join(outputdir, "cut")
        cut_cook_config(
            expanded_app_path, cutpath_app_path, appname, cutoutpath_app_path
        )
    elif pargs.base:
        logger.info(f"Applying to base")
        basedir = os.path.join(outputdir, "base")
        os.mkdir(basedir)
        shutil.copy(local_filename, os.path.join(basedir, appname + ".tgz"))

    if pargs.sh:
        logger.info(f"Applying to sh {pargs.sh}")
        droot = os.path.join(outputdir, "sh")
        os.mkdir(droot)
        if "base" in pargs.sh:
            os.mkdir(os.path.join(droot, "base"))
            shutil.copy(
                local_filename,
                os.path.join(os.path.join(droot, "base"), appname + ".tgz"),
            )
        else:
            for d in pargs.sh:
                os.mkdir(os.path.join(droot, d))
                shutil.copy(
                    local_filename,
                    os.path.join(os.path.join(droot, d), appname + ".tgz"),
                )

    if pargs.idxc:
        logger.info(f"Applying to idxc {pargs.idxc}")
        droot = os.path.join(outputdir, "idxc")
        os.mkdir(droot)
        for d in pargs.idxc:
            os.mkdir(os.path.join(droot, d))
            shutil.copy(
                local_filename, os.path.join(os.path.join(droot, d), appname + ".tgz")
            )

    if pargs.fwd:
        logger.info(f"Applying to fwd {pargs.fwd}")
        droot = os.path.join(outputdir, "fwd")
        os.mkdir(droot)
        if "base" in pargs.fwd:
            os.mkdir(os.path.join(droot, "base"))
            shutil.copy(
                local_filename,
                os.path.join(os.path.join(droot, "base"), appname + ".tgz"),
            )
        else:
            for d in pargs.sh:
                os.mkdir(os.path.join(droot, d))
                shutil.copy(
                    local_filename,
                    os.path.join(os.path.join(droot, d), appname + ".tgz"),
                )

    # result = list(Path(outputdir).rglob("*.tgz"))
    result = glob.glob(outputdir + "/**/*.tgz", recursive=True)
    if pargs.s3endpoint:
        # s3 = boto3.client('s3',endpoint_url=pargs.s3endpoint)
        s3 = boto3.resource("s3", endpoint_url=pargs.s3endpoint)
    else:
        s3 = boto3.resource("s3")

    for r in result:
        relative = (pargs.s3root + "/").replace("//", "/") + r.replace(
            outputdir + "/", ""
        )
        # s3.upload_file(r,pargs.s3bucket,relative)
        s3.Bucket(pargs.s3bucket).upload_file(r, relative)
        logger.info(relative)


if __name__ == "__main__":

    with tempfile.TemporaryDirectory() as tmpdirname:
        main(tmpdirname)
        logger.info(f"output {tmpdirname}")
