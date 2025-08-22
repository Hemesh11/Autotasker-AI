"""
AWS CloudFormation template for AutoTasker AI infrastructure
Defines all required AWS resources in Infrastructure as Code
"""

import json
from typing import Dict, Any


class CloudFormationTemplate:
    """Generates CloudFormation template for AutoTasker AI"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration"""
        self.config = config
        self.aws_config = config.get('aws', {})
        
    def generate_template(self) -> Dict[str, Any]:
        """Generate complete CloudFormation template"""
        template = {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Description": "AutoTasker AI - Complete serverless infrastructure",
            "Parameters": self._get_parameters(),
            "Resources": self._get_resources(),
            "Outputs": self._get_outputs()
        }
        
        return template
    
    def _get_parameters(self) -> Dict[str, Any]:
        """Define CloudFormation parameters"""
        return {
            "ProjectName": {
                "Type": "String",
                "Default": "AutoTaskerAI",
                "Description": "Name of the project"
            },
            "Environment": {
                "Type": "String",
                "Default": "production",
                "AllowedValues": ["development", "staging", "production"],
                "Description": "Deployment environment"
            },
            "LLMProvider": {
                "Type": "String",
                "Default": "openrouter",
                "Description": "LLM provider (openrouter or openai)"
            },
            "LLMApiKey": {
                "Type": "String",
                "NoEcho": True,
                "Description": "API key for LLM service"
            },
            "FromEmail": {
                "Type": "String",
                "Description": "Email address for sending notifications"
            },
            "ToEmail": {
                "Type": "String",
                "Description": "Default recipient email address"
            }
        }
    
    def _get_resources(self) -> Dict[str, Any]:
        """Define all AWS resources"""
        return {
            # S3 Bucket for logs and artifacts
            "LogsBucket": {
                "Type": "AWS::S3::Bucket",
                "Properties": {
                    "BucketName": {"Fn::Sub": "${ProjectName}-logs-${Environment}"},
                    "VersioningConfiguration": {"Status": "Enabled"},
                    "LifecycleConfiguration": {
                        "Rules": [{
                            "Id": "DeleteOldLogs",
                            "Status": "Enabled",
                            "ExpirationInDays": 90
                        }]
                    },
                    "PublicAccessBlockConfiguration": {
                        "BlockPublicAcls": True,
                        "BlockPublicPolicy": True,
                        "IgnorePublicAcls": True,
                        "RestrictPublicBuckets": True
                    }
                }
            },
            
            # DynamoDB table for execution metadata
            "ExecutionTable": {
                "Type": "AWS::DynamoDB::Table",
                "Properties": {
                    "TableName": {"Fn::Sub": "${ProjectName}-executions-${Environment}"},
                    "BillingMode": "PAY_PER_REQUEST",
                    "AttributeDefinitions": [{
                        "AttributeName": "task_id",
                        "AttributeType": "S"
                    }],
                    "KeySchema": [{
                        "AttributeName": "task_id",
                        "KeyType": "HASH"
                    }],
                    "TimeToLiveSpecification": {
                        "AttributeName": "ttl",
                        "Enabled": True
                    },
                    "PointInTimeRecoverySpecification": {
                        "PointInTimeRecoveryEnabled": True
                    }
                }
            },
            
            # IAM Role for Lambda
            "LambdaExecutionRole": {
                "Type": "AWS::IAM::Role",
                "Properties": {
                    "RoleName": {"Fn::Sub": "${ProjectName}-lambda-role-${Environment}"},
                    "AssumeRolePolicyDocument": {
                        "Version": "2012-10-17",
                        "Statement": [{
                            "Effect": "Allow",
                            "Principal": {"Service": "lambda.amazonaws.com"},
                            "Action": "sts:AssumeRole"
                        }]
                    },
                    "ManagedPolicyArns": [
                        "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
                    ],
                    "Policies": [{
                        "PolicyName": "AutoTaskerExecutionPolicy",
                        "PolicyDocument": {
                            "Version": "2012-10-17",
                            "Statement": [
                                {
                                    "Effect": "Allow",
                                    "Action": [
                                        "s3:GetObject",
                                        "s3:PutObject",
                                        "s3:DeleteObject"
                                    ],
                                    "Resource": {"Fn::Sub": "${LogsBucket}/*"}
                                },
                                {
                                    "Effect": "Allow",
                                    "Action": [
                                        "dynamodb:GetItem",
                                        "dynamodb:PutItem",
                                        "dynamodb:UpdateItem",
                                        "dynamodb:DeleteItem",
                                        "dynamodb:Query",
                                        "dynamodb:Scan"
                                    ],
                                    "Resource": {"Fn::GetAtt": ["ExecutionTable", "Arn"]}
                                },
                                {
                                    "Effect": "Allow",
                                    "Action": [
                                        "ses:SendEmail",
                                        "ses:SendRawEmail"
                                    ],
                                    "Resource": "*"
                                },
                                {
                                    "Effect": "Allow",
                                    "Action": [
                                        "logs:CreateLogGroup",
                                        "logs:CreateLogStream",
                                        "logs:PutLogEvents"
                                    ],
                                    "Resource": "arn:aws:logs:*:*:*"
                                }
                            ]
                        }
                    }]
                }
            },
            
            # Lambda Layer for dependencies
            "DependenciesLayer": {
                "Type": "AWS::Lambda::LayerVersion",
                "Properties": {
                    "LayerName": {"Fn::Sub": "${ProjectName}-dependencies-${Environment}"},
                    "Description": "Python dependencies for AutoTasker AI",
                    "Content": {
                        "S3Bucket": {"Ref": "LogsBucket"},
                        "S3Key": "layers/dependencies.zip"
                    },
                    "CompatibleRuntimes": ["python3.9", "python3.10", "python3.11"]
                }
            },
            
            # Lambda function
            "AutoTaskerFunction": {
                "Type": "AWS::Lambda::Function",
                "Properties": {
                    "FunctionName": {"Fn::Sub": "${ProjectName}-runner-${Environment}"},
                    "Runtime": "python3.9",
                    "Handler": "aws.lambda_handler.lambda_handler",
                    "Role": {"Fn::GetAtt": ["LambdaExecutionRole", "Arn"]},
                    "Code": {
                        "S3Bucket": {"Ref": "LogsBucket"},
                        "S3Key": "functions/autotasker.zip"
                    },
                    "Layers": [{"Ref": "DependenciesLayer"}],
                    "Timeout": 300,
                    "MemorySize": 512,
                    "Environment": {
                        "Variables": {
                            "LLM_PROVIDER": {"Ref": "LLMProvider"},
                            "LLM_API_KEY": {"Ref": "LLMApiKey"},
                            "LLM_MODEL": "openai/gpt-3.5-turbo",
                            "S3_BUCKET": {"Ref": "LogsBucket"},
                            "DYNAMODB_TABLE": {"Ref": "ExecutionTable"},
                            "FROM_EMAIL": {"Ref": "FromEmail"},
                            "TO_EMAIL": {"Ref": "ToEmail"},
                            "AWS_REGION": {"Ref": "AWS::Region"}
                        }
                    },
                    "ReservedConcurrencyLimit": 10
                }
            },
            
            # EventBridge role
            "EventBridgeRole": {
                "Type": "AWS::IAM::Role",
                "Properties": {
                    "AssumeRolePolicyDocument": {
                        "Version": "2012-10-17",
                        "Statement": [{
                            "Effect": "Allow",
                            "Principal": {"Service": "events.amazonaws.com"},
                            "Action": "sts:AssumeRole"
                        }]
                    },
                    "Policies": [{
                        "PolicyName": "InvokeLambdaPolicy",
                        "PolicyDocument": {
                            "Version": "2012-10-17",
                            "Statement": [{
                                "Effect": "Allow",
                                "Action": "lambda:InvokeFunction",
                                "Resource": {"Fn::GetAtt": ["AutoTaskerFunction", "Arn"]}
                            }]
                        }
                    }]
                }
            },
            
            # Lambda permission for EventBridge
            "LambdaInvokePermission": {
                "Type": "AWS::Lambda::Permission",
                "Properties": {
                    "FunctionName": {"Ref": "AutoTaskerFunction"},
                    "Action": "lambda:InvokeFunction",
                    "Principal": "events.amazonaws.com"
                }
            },
            
            # CloudWatch Log Group
            "AutoTaskerLogGroup": {
                "Type": "AWS::Logs::LogGroup",
                "Properties": {
                    "LogGroupName": {"Fn::Sub": "/aws/lambda/${AutoTaskerFunction}"},
                    "RetentionInDays": 14
                }
            },
            
            # CloudWatch Dashboard
            "AutoTaskerDashboard": {
                "Type": "AWS::CloudWatch::Dashboard",
                "Properties": {
                    "DashboardName": {"Fn::Sub": "${ProjectName}-dashboard-${Environment}"},
                    "DashboardBody": {"Fn::Sub": json.dumps({
                        "widgets": [
                            {
                                "type": "metric",
                                "x": 0, "y": 0,
                                "width": 12, "height": 6,
                                "properties": {
                                    "metrics": [
                                        ["AWS/Lambda", "Invocations", "FunctionName", "${AutoTaskerFunction}"],
                                        [".", "Errors", ".", "."],
                                        [".", "Duration", ".", "."]
                                    ],
                                    "period": 300,
                                    "stat": "Sum",
                                    "region": "${AWS::Region}",
                                    "title": "Lambda Metrics"
                                }
                            },
                            {
                                "type": "log",
                                "x": 0, "y": 6,
                                "width": 24, "height": 6,
                                "properties": {
                                    "query": "SOURCE '/aws/lambda/${AutoTaskerFunction}'\n| fields @timestamp, @message\n| sort @timestamp desc\n| limit 100",
                                    "region": "${AWS::Region}",
                                    "title": "Recent Executions"
                                }
                            }
                        ]
                    })}
                }
            }
        }
    
    def _get_outputs(self) -> Dict[str, Any]:
        """Define CloudFormation outputs"""
        return {
            "LambdaFunctionArn": {
                "Description": "ARN of the AutoTasker Lambda function",
                "Value": {"Fn::GetAtt": ["AutoTaskerFunction", "Arn"]},
                "Export": {"Name": {"Fn::Sub": "${ProjectName}-lambda-arn-${Environment}"}}
            },
            "S3BucketName": {
                "Description": "Name of the S3 bucket for logs",
                "Value": {"Ref": "LogsBucket"},
                "Export": {"Name": {"Fn::Sub": "${ProjectName}-bucket-${Environment}"}}
            },
            "DynamoDBTableName": {
                "Description": "Name of the DynamoDB table",
                "Value": {"Ref": "ExecutionTable"},
                "Export": {"Name": {"Fn::Sub": "${ProjectName}-table-${Environment}"}}
            },
            "DashboardURL": {
                "Description": "CloudWatch Dashboard URL",
                "Value": {"Fn::Sub": "https://${AWS::Region}.console.aws.amazon.com/cloudwatch/home?region=${AWS::Region}#dashboards:name=${AutoTaskerDashboard}"}
            }
        }
    
    def save_template(self, filename: str = "autotasker-infrastructure.json") -> str:
        """Save template to file"""
        template = self.generate_template()
        
        filepath = f"aws/{filename}"
        with open(filepath, 'w') as f:
            json.dump(template, f, indent=2)
        
        print(f"✅ CloudFormation template saved to: {filepath}")
        return filepath


def generate_cloudformation_template(config_path: str = "config/config.yaml") -> str:
    """Generate and save CloudFormation template"""
    from backend.utils import load_config
    
    config = load_config(config_path)
    template_generator = CloudFormationTemplate(config)
    
    return template_generator.save_template()


if __name__ == "__main__":
    # Generate template
    template_file = generate_cloudformation_template()
    
    print("\n🚀 CloudFormation template generated!")
    print(f"📁 Template file: {template_file}")
    print("\nTo deploy using AWS CLI:")
    print(f"aws cloudformation create-stack --stack-name autotasker-ai --template-body file://{template_file} --capabilities CAPABILITY_NAMED_IAM --parameters ParameterKey=LLMApiKey,ParameterValue=your-api-key ParameterKey=FromEmail,ParameterValue=your-email@domain.com ParameterKey=ToEmail,ParameterValue=recipient@domain.com")
