import "source-map-support/register";
import * as cdk from "aws-cdk-lib";
import { BeaconNetworkStack } from "./beacon-network-stack";

const app = new cdk.App();

/**
 * Stack for UMCCR dev
 */
new BeaconNetworkStack(app, "BeaconNetworkUmccrDev", {
  env: {
    account: "843407916570",
    region: "ap-southeast-2",
  },
  description: "HGPP Beacon Network",
  tags: {
    "umccr-org:Stack": "BeaconNetworkUmccrDev",
    "umccr-org:Product": "BeaconNetwork",
  },
  secretArn:
    "arn:aws:secretsmanager:ap-southeast-2:843407916570:secret:BeaconNetwork-zWANqf",
  deployUrl: "https://beacon-network.dev.umccr.org",
});

/**
 * Stack for Australian Biocommons
 */
new BeaconNetworkStack(app, "BeaconNetworkAustralianBiocommonsProd", {
  env: {
    account: "0000",
    region: "ap-southeast-2",
  },
  description: "HGPP Beacon Network",
  tags: {},
  secretArn: "arn:aws:secretsmanager:ap-southeast-2:0000:secret:XYZ",
  deployUrl: "https://beacon-network.biocommons.org.au",
});
