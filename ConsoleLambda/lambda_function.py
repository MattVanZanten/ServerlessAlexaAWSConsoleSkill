from __future__ import print_function
import boto3
from botocore.exceptions import ClientError
import logging

ec2_details = boto3.resource('ec2')
ec2_control = boto3.client('ec2')

logger = logging.getLogger()
logger.setLevel(logging.INFO)
def my_logging_handler(event, context):
    logger.info('got event{}'.format(event))
    logger.error('something went wrong')
    return 'Hello World!'  


def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    #if (event['session']['application']['applicationId'] !=
    #        "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #    raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])


def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'] + " Intent=" + intent_request['intent']['name'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "Describe":
        return get_instances_by_tag_value(intent, session)
    elif intent_name == "Start":
        return change_instances_state_by_tag_value(intent, session, "start")
    elif intent_name == "Stop":
        return change_instances_state_by_tag_value(intent, session, "stop")
    elif intent_name == "Reboot":
        return change_instances_state_by_tag_value(intent, session, "reboot")

    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.
    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here

# --------------- Functions that control the skill's behavior ------------------


def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to the Alexa Console Skill. " \
                    "Please tell me what to describe, start, stop or reboot."
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Please tell me what to describe, start, stop or reboot."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def create_describe_attributes(instance_id):
    return {"InstanceId": instance_id}


def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': 'SessionSpeechlet - ' + title,
            'content': 'SessionSpeechlet - ' + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


def get_instances_by_tag_value(intent, session):

    card_title = intent['name']
    tag = intent['slots']['Text']['value']

    session_attributes = {}
    should_end_session = True

    reprompt_text = "I did not quite get that." \
                "I can describe instance details if you say. " \
                "Alexa, tell console to describe name tag."

    instances = ec2_details.instances.filter(Filters=[{'Name': 'tag:Name', 'Values': [tag]}])
    for instance in instances:
            print(instance.id, instance.instance_type)
            instance_id = instance.id
            session_attrubutes = create_describe_attributes(instance_id)
            speech_output = "Instance ID for " + tag + " is. " + instance_id
            
            return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def change_instances_state_by_tag_value(intent, session, state):

    card_title = intent['name']
    tag = intent['slots']['Text']['value']

    session_attributes = {}
    should_end_session = True

    reprompt_text = "I did not quite get that." \
                "I can start an instance if you say. " \
                "Alexa, tell console to " + state + " name tag."

    instances = ec2_details.instances.filter(Filters=[{'Name': 'tag:Name', 'Values': [tag]}])
    for instance in instances:
            print(instance.id, instance.instance_type)
            
            if state == "stop":
                ec2_control.stop_instances(InstanceIds=[instance.id], DryRun=False)
                speech_output = "Instance with tag. " + tag + ". is stopping."
            elif state == "reboot":
                ec2_control.reboot_instances(InstanceIds=[instance.id], DryRun=False)
                speech_output = "Instance with tag. " + tag + ". is rebooting."
            else:
                ec2_control.start_instances(InstanceIds=[instance.id], DryRun=False)
                speech_output = "Instance with tag. " + tag + ". is starting."

            return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))