import { aws_ecs as ecs, CfnOutput } from "aws-cdk-lib";
import { Construct } from "constructs";
import { DockerImageAsset, Platform } from "aws-cdk-lib/aws-ecr-assets";
import { Role, ServicePrincipal } from "aws-cdk-lib/aws-iam";
import { Secret } from "aws-cdk-lib/aws-secretsmanager";
import * as apprunner from "@aws-cdk/aws-apprunner-alpha";
import { join } from "path";
import { BeaconNetworkProps } from "./beacon-network-props";
import { smartVpcConstruct } from "./vpc";
import { SubnetType } from "aws-cdk-lib/aws-ec2";

/**
 */
export class BeaconNetworkAppRunnerConstruct extends Construct {
  constructor(scope: Construct, id: string, props: BeaconNetworkProps) {
    super(scope, id);

    // construct a new VPC with NAT
    const vpc = smartVpcConstruct(this, "VPC", null, false);

    const vpcConnector = new apprunner.VpcConnector(this, "VpcConnector", {
      vpc: vpc,
      vpcSubnets: vpc.selectSubnets({
        subnetType: SubnetType.PRIVATE_WITH_EGRESS,
      }),
    });

    const secret = Secret.fromSecretPartialArn(this, "Secret", props.secretArn);

    const asset = new DockerImageAsset(this, "DockerImageAsset", {
      directory: join(__dirname, "..", ".."),
      platform: Platform.LINUX_AMD64,
      buildArgs: {},
    });

    const role = new Role(this, "ServiceRole", {
      assumedBy: new ServicePrincipal("tasks.apprunner.amazonaws.com"),
    });
    secret.grantRead(role);
    secret.grantRead(new ServicePrincipal("tasks.apprunner.amazon.com"));

    const appService = new apprunner.Service(this, "Service", {
      source: apprunner.Source.fromAsset({
        imageConfiguration: {
          port: 8080,
          environmentSecrets: {
            CLIENT_ID: ecs.Secret.fromSecretsManager(secret, "clientId"),
            CLIENT_SECRET: ecs.Secret.fromSecretsManager(
              secret,
              "clientSecret"
            ),
            SESSION_SECRET: ecs.Secret.fromSecretsManager(
              secret,
              "sessionSecret"
            ),
            JWT_PEM: ecs.Secret.fromSecretsManager(secret, "jwtPem"),
            LOGIN_SERVER: ecs.Secret.fromSecretsManager(secret, "loginServer"),
          },
          environmentVariables: {
            DEPLOY_URL: props.deployUrl,
          },
        },
        asset: asset,
      }),
      instanceRole: role,
      autoDeploymentsEnabled: false,
      vpcConnector: vpcConnector,
    });

    new CfnOutput(this, "DeployUrl", {
      value: appService.serviceUrl,
    });
  }
}
