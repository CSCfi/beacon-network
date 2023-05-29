import {Stack, StackProps} from "aws-cdk-lib";
import {Construct} from "constructs";
import {BeaconNetworkProps} from "./beacon-network-props";
import {BeaconNetworkAppRunnerConstruct} from "./beacon-network-app-runner";

/**
 */
export class BeaconNetworkStack extends Stack {
  constructor(
    scope: Construct,
    id: string,
    props: StackProps & BeaconNetworkProps
  ) {
    super(scope, id, props);

    const app = new BeaconNetworkAppRunnerConstruct(this, "App", props)
  }
}

