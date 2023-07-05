import { aws_ecs as ecs, CfnOutput, Stack } from "aws-cdk-lib";
import { Construct } from "constructs";
import { DockerImageAsset, Platform } from "aws-cdk-lib/aws-ecr-assets";
import {
  Policy,
  PolicyStatement,
  Role,
  ServicePrincipal,
} from "aws-cdk-lib/aws-iam";
import { Secret } from "aws-cdk-lib/aws-secretsmanager";
import * as apprunner from "@aws-cdk/aws-apprunner-alpha";
import { join } from "path";
import { BeaconNetworkProps } from "./beacon-network-props";

/**
 */
export class BeaconNetworkAppRunnerConstruct extends Construct {
  constructor(scope: Construct, id: string, props: BeaconNetworkProps) {
    super(scope, id);

    const secret = Secret.fromSecretPartialArn(this, "Secret", props.secretArn);

    const asset = new DockerImageAsset(this, "DockerImageAsset", {
      directory: join(__dirname, "..", ".."),
      platform: Platform.LINUX_AMD64,
      buildArgs: {},
    });

    const policy = this.createPolicy();

    const role = new Role(this, "ServiceRole", {
      assumedBy: new ServicePrincipal("tasks.apprunner.amazonaws.com"),
    });
    secret.grantRead(role);
    secret.grantRead(new ServicePrincipal("tasks.apprunner.amazon.com"))

    role.attachInlinePolicy(policy);

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
          },
          environmentVariables: {
            DEPLOY_URL: props.deployUrl,
          },
        },
        asset: asset,
      }),
      instanceRole: role,
      autoDeploymentsEnabled: false,
    });

    new CfnOutput(this, "DeployUrl", {
      value: appService.serviceUrl,
    });
  }

  private createPolicy(): Policy {
    const policy = new Policy(this, "ServiceTaskPolicy");

    // need to be able to fetch secrets as we spin up in app runner
    policy.addStatements(
      new PolicyStatement({
        actions: ["secretsmanager:GetSecretValue"],
        resources: [
          `arn:aws:secretsmanager:${Stack.of(this).region}:${
            Stack.of(this).account
          }:secret:BeaconNetwork*`,
        ],
      })
    );

    return policy;
  }
}
