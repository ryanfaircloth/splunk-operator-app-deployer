# splunk-operator-app-deployer

The app deployer will deploy app packages to S3 for Splunk operator

## Usage

To deploy apps from Splunk base a username and password must be stored as a secret

```bash
#This username and password must be "api" enabled and should not have write access to any apps on Splunkbase
kubectl -n splunk create secret generic splunkbase-secret \
    --from-literal=SPLUNK_BASE_USER=produser \
    --from-literal=SPLUNK_BASE_PASSWORD=<password>
```

The following example layout can be used to support a "complex" multi search head environment with ITSI and ES

```bash
    ├── bucketroot
    │   ├── cut # Index time configuration extracted from an app for indexer and intermediate forwarder use formerly known as slim. CUT add-ons will be applied to idxc and all fwd roles except for hwf-* where full add-ons must be used.
    │   ├── base # Base configurations applied to all instances regardless of role
    │   ├── sh
    │   │   ├── base #base configuration applied to all SH deployments
    │   │   ├── itoa #Configuration applied to the ITE/Work or ITSI Instance
    │   │   ├── itoa-deployer #Configuration applied to the ITE/Work or ITSI Instance by staging on the deployer
    │   │   ├── es   #Configuration applied to the ES Instance
    │   │   ├── es-deployer #Configuration applied to the ES Instance by staging on the deployer
    │   │   ├── <special>   # applied to special additional roles not typically used
    │   │   ├── <special>-staged #Configuration applied to the special Instance by staging on the deployer
    │   ├── idxc
    │   │   ├── base-cm #base configuration applied to all cms
    │   │   ├── base-idxp #base configuration applied to all idx peers via master apps
    │   │   ├── default # configuration applied to all idxcm deployments
    │   │   ├── default-idxp # configuration applied to all idxp via master apps
    │   │   ├── <special>   # applied to special additional roles not typically used
    │   │   ├── <special>-idxp #Configuration applied to the special Instance by staging on the deployer
    │   ├── fwd
    │   │   ├── base #base configuration applied to all fwd deployments
    │   │   ├── s2s  # s2s IF
    │   │   ├── hec  # hec IF Primary event based hec input
    │   │   ├── hecraw  # hec raw IF Less used HEC "raw" event input
    │   │   ├── hecack  # hec withack IF rarely used and discouraged hec with ack input
    │   │   ├── hwf-<special> Heavy forwarders typically used to pull based inputs such as DBX and JMX
    │   ├── ds
    │   │   ├── base #base configuration applied to all ds deployments via apps
    │   │   ├── apps #base configuration applied to all ds deployments via deployment-apps

## Deploy an add-on from Splunk base

```bash
#Release name must use a valid dns format name (a-z 0-9 -)
helm upgrade --install \
    --namespace splunk \
    -f examples/ta.yaml \
    splunk-ta-windows \
    charts/splunk-operator-app-deployer
```

## Options

The deployment "job" can be configured using CLI switces in the cmd portion of the manifest

```bash
--cut #this option prunes all config from the package that is not used in Splunk Indexing and deployes to the "cut" directory within the bucket. When using this option only --sh and --fwd hwf* arguments should be used
--sh <placement> #see placement list above can be listed more than once to select multiple locations "base" should be used alone
--idxc <placement> #see placement list above can be listed more than once to select multiple locations "base" should be used alone
--fwd <placement> #see placement list above can be listed more than once to select multiple locations "base" should be used alone
--ds <placement> #see placement list above can be listed more than once to select multiple locations "base" should be used alone

--s3endpoint #optional uri for s3 endpoint typically used outside of aws
--s3bucket #bucket name required
--s3root #root folder within bucket required

--source #One of
         #http/https url without authentication
         #splunkbase://<id>/version requires secret numeric splunk base id and public version
         #warning Splunk base versions may be hidden/removed at any time best practice is to utilize a local artifact server
```
