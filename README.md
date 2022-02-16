# splunk-operator-app-deployer

The app deployer will deploy app packages to S3 for Splunk operator

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
