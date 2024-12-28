# Alexa-Google-Doc-Viewer
This is a Alexa skill myself and ChatGPT helped me work on. Basically, I wanted the ability to digitally store all of my wife's recipes in Google Drive and view them on an Echo Show device in our kitchen. I wanted to do this without using the built-in Silk browser on the Echo Show (which isn't great) Thought this code may help someone else out.

Some basic instructions (I will flesh this out a bit more in the future, I have some more functionality I want to add to this)

You need to create an Alexa developer account and create a custom skill. When going through the skill setup wizard, you will want to create a custom skill from scratch and use the hosted python option so you don't have to setup an AWS account.

You will need to go to Google Cloud Console and create a project and get a Google Drive API key and you'll need to paste that key into the lambda_function.py code in the skill. You will also need to choose a folder in your Google Drive to use for your recipes. I have this setup to first display recipe categories, so I have all of my actual recipe docs in their respective recipe category folder. The root Google Drive folder will need to be set to viewable by anyone with the link. In the URL of the root folder, you will need the last part of it. So for instance, your URL will look like this: https://drive.google.com/drive/u/0/folders/copy_this_part Once you have that part copied, you'll need to put it in your lambda code as the ROOT_FOLDER_ID. 

So in the skill, you'll need to set a skill invocation name. I use "Jessie's Kitchen" so I say "Alexa, open Jessie's Kitchen" to open the skill.

You'll need to setup a few custom Intents as well. I currently have a scrolldown intent, scrollup intent, and a set timer intent.

In Interfaces, you'll need to turn on the Alexa Presentation Language (APL) 

Under Permissions, you'll need to turn on the timers option.

You can go to the test section, put it in Developer mode and try it out!

Again, I will at some point in the future update and flesh this README out a little more, I have a couple of things I want to add to the skill and then some error logging cleanup to save on API requests in Alexa.
