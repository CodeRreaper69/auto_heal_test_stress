# AWS AUTO HEAL INFRASTRUCTURE 

1) I will test them on my local system first!
2) I will try to put some stress tests on my CPU through and see if the agents by gathering my running process lists, logs and all can assess, what exact command to run.
3) After doing this, the agents will propose me the required changes to be done for auto healing part 
4) After this, I will approve those things, as the agents will offer me a thorough summarized of what to be done, once I will allow it, they will execute it on their own 
5) For this, I will try to mimic what will happen with AWS 
6) For the UI I will try to run Streamlit for it
7) For the agents, I will use langchain, langgraph if possible? or customs
Scripts - 
	1) One will be the monitoring agent, a script which will constantly monitor the system, see changes, spikes and all if any, if there is, updates me. (Like the cloudwatch)
	2) The other will be a the debug agent which will monitor those said by the monitoring agent.
	3) After the Debug agent will assess the things mentioned by monitoring agent, it will state remedies
	4) Now these remedies will get passed on to the validator ( in this case it will be me, I will be giving the validation for execution), if it flags as True, then goes to Execution Agent
	otherwise it moves to Escalation agent which will eventually hand it over to me and they will leave the system access
	5) After the execution agent, the system will log this to a database ( the Knowledge base ) so that if events like this occurs, similar ( or same ) diagnosis can be performed.
	6) For each step there will be a agent log, which will monitor the logs or doings of what they are doing.
	
	
For Local, I will be using Gemini LLM 
Each agent Must contact with themselves 
	
Places where there needs agentic Auto Heal - 
1) HIGH CPU Utilisation 
2) High Storage usage detected



For Production - 
What is my idea - 
I will collect documents mentioning used cases and corresponding solutions 
Extract meaningful information from them and then will fine tune models on bedrock
The embeddings which I will be creating from them, will also be used as RAG
This Debugging agent will debug the problem based on this historical fixes which cloud/devops engineers do generally.
After the debug agent proposes a solution, we will then create ground truth agents for the same. which is the validator, which will measure how much correct solution, the debug agent has provided.
So there will be two approaches - 
Using RAG and Using Fine Tunes LLMs.
