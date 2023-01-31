import pulumi
import pulumi_aws as aws
import pulumi_aws_native as aws_native
from pulumi import ResourceOptions
import json

SECONDARY_REGION = "us-east-1"
DESTINATION_ACCOUNT = <DESTINATION_ACCOUNT_ID>
ROLE_NAME = <ROLE_NAME>
SOURCE_ACCOUNT = <SOURCE_ACCOUNT_ID>

# creating provider for destination account
destination_provider = aws.Provider(
    "provider_destination_account",
    region=SECONDARY_REGION,
    assume_role=aws.ProviderAssumeRoleArgs(
        role_arn=f"arn:aws:iam::{DESTINATION_ACCOUNT}:role/{ROLE_NAME}",
    ),
)


def ecr_repo(repo_name):
    repo = aws.ecr.Repository(
        f"{repo_name}",
        image_scanning_configuration=aws.ecr.RepositoryImageScanningConfigurationArgs(
            scan_on_push=True,
        ),
        name=repo_name,
        image_tag_mutability="MUTABLE",
    )


def ecr_repo_config():
    repo_replication_config = aws.ecr.ReplicationConfiguration(
        "source_repo_replication_config",
        replication_configuration=aws.ecr.ReplicationConfigurationReplicationConfigurationArgs(
            rules=[
                aws.ecr.ReplicationConfigurationReplicationConfigurationRuleArgs(
                    destinations=[
                        aws.ecr.ReplicationConfigurationReplicationConfigurationRuleDestinationArgs(
                            region=SECONDARY_REGION,
                            registry_id=DESTINATION_ACCOUNT,
                        )
                    ],
                    repository_filters=[
                        aws.ecr.ReplicationConfigurationReplicationConfigurationRuleRepositoryFilterArgs(
                            filter="prod-",
                            filter_type="PREFIX_MATCH",
                        )
                    ],
                )
            ],
        ),
    )


def registry_permission():
    aws.ecr.RegistryPolicy(
        "registry_permission",
        policy=json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "access-from-source-account",
                        "Effect": "Allow",
                        "Principal": {"AWS": f"arn:aws:iam::{SOURCE_ACCOUNT}:root"},
                        "Action": ["ecr:CreateRepository", "ecr:ReplicateImage"],
                        "Resource": f"arn:aws:ecr:{SECONDARY_REGION}:{DESTINATION_ACCOUNT}:repository/*",
                    }
                ],
            }
        ),
        opts=pulumi.ResourceOptions(provider=destination_provider),
    )


ecr_repo("prod-1")
ecr_repo("prod-2")
ecr_repo("prod-3")
ecr_repo("prod-4")
ecr_repo_config()
registry_permission()
