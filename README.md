### Text to CAD. 

The way this works is it generates python code via gpt4 which generates the requested geometry. 
From the python script I parse all the relevant parameters and generate a just in time UI. Here is a small demo. Note that its not very reliable for complex parts.
I think for more complex tasks trying to 1-shot the solution is too difficult. It would probably be good to mimic what humans do and introduce a feedback loop. 
I think it should be possible to make an agent that first comes up with steps to model a part and then executes each step while analyzing the result of each step using gpt4-vision and possibly fixing any mistakes. 
![cad_llm](https://github.com/Janos95/manifold_llm/assets/19853534/d7a8d7f4-4479-4ace-baa5-5f022f6b106e)

Its also surprisingly good with chairs (or maybe not so surprisingly given that the prompt contains an example of an L-bracket)

![chair_llm](https://github.com/Janos95/manifold_llm/assets/19853534/d2c9c551-d73c-4df4-9f2c-b65b98b63805)
