import { StackProps, Tags } from "aws-cdk-lib";
import { Construct } from "constructs";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import {
  InterfaceVpcEndpointAwsService,
  IVpc,
  SubnetType,
} from "aws-cdk-lib/aws-ec2";

/**
 * The smart VPC construct allows us to either inherit an existing VPC, or create a new VPC
 * based purely on the name or id passed in.
 *
 * @param scope
 * @param id
 * @param vpcNameOrDefaultOrNull either an existing VPC id, the string "default" to indicate to let CDK pick the VPC, or null to indicate a new VPC should be created
 * @param enableEcrEndpoints if creating a new VPC, this indicates whether we should install the endpoints to enable private ECR
 */
export function smartVpcConstruct(
  scope: Construct,
  id: string,
  vpcNameOrDefaultOrNull: string | "default" | null,
  enableEcrEndpoints: boolean
): IVpc {
  // if not vpc details are given then we construct a new VPC
  if (!vpcNameOrDefaultOrNull) {
    const vpc = new NatVPC(scope, id);

    // btw https://github.com/aws/aws-cdk/issues/19332
    // in case you wonder why these are not tagged automatically
    // https://github.com/aws-cloudformation/cloudformation-coverage-roadmap/issues/196

    const addEndpoint = (
      name: string,
      service: InterfaceVpcEndpointAwsService
    ) => {
      const ecrEndpoint = vpc.addInterfaceEndpoint(name + "Endpoint", {
        service: service,
        privateDnsEnabled: true,
        subnets: {
          subnetType: SubnetType.PRIVATE_ISOLATED,
        },
      });
    };

    if (enableEcrEndpoints) {
      addEndpoint("Ecr", InterfaceVpcEndpointAwsService.ECR);
      addEndpoint("EcrDkr", InterfaceVpcEndpointAwsService.ECR_DOCKER);
      addEndpoint("Logs", InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS);
    }

    return vpc;
  }

  // if they ask for the special name default then we use the VPC defaulting mechanism (via CDK lookup)
  if (vpcNameOrDefaultOrNull === "default")
    return ec2.Vpc.fromLookup(scope, id, {
      isDefault: true,
    });

  // otherwise look up the actual name given
  return ec2.Vpc.fromLookup(scope, id, {
    vpcName: vpcNameOrDefaultOrNull,
  });
}
class NatVPC extends ec2.Vpc {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, {
      maxAzs: 99, // 99 will mean that the VPC expands to consume as many AZs as it can in the region
      natGateways: 1,
      subnetConfiguration: [
        {
          name: "ingress",
          subnetType: ec2.SubnetType.PUBLIC,
        },
        {
          name: "application",
          subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
        },
        {
          name: "database",
          subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
        },
      ],
      enableDnsHostnames: true,
      enableDnsSupport: true,
      // gateway endpoints are free and help avoid NAT traffic... there is no point in
      // not having them by default
      gatewayEndpoints: {
        S3: {
          service: ec2.GatewayVpcEndpointAwsService.S3,
        },
        Dynamo: {
          service: ec2.GatewayVpcEndpointAwsService.DYNAMODB,
        },
      },
    });
  }
}
