# Introduction 
The tool calculates the health score of open source packages. Under 50% is a very low score which usually indicates insufficiently maintained or abandoned packages. 50% - 60% is still quite a low score and usually the packages in question are insufficiently maintained as well.  
Furthermore, the tool gives various warnings that could flag insufficiently maintained packages, abandoned ones, hostile takeover through maintainer domain hijack, and malicious packages (no malware detection present, only flagging packages that are very fresh or have 0 previous versions).  
TODO: Add formula and describe the markers
# Getting Started
## Usage:
### 1. As a desktop application using GUI:  
**Run the main.py script.**  
In the initial GUI window that is displayed, it is possible to choose 4 different ecosystems (PyPi, npm, Maven and conda). Then, simply write the name of the package in question, click calculate health score, and the result will be displayed along with the warning messages (if there are any).  
**Click the "configure" button.**  
By clicking the configure button, a new GUI window opens. There, you can see formula, markers, weights, thresholds and explanations based on which the score is calculated. Moreover, you can change any of the marker weights or thresholds based on your preferances. You have to click the save button at the bottom or the changes will not be saved and will not be used with the new package score calculation. It is also possible to revert to default values at any time, by simply clicking the default button above each column (weights, thresholds).   
Finally, there is an option to use AI calculated optimal weights. However, due to the limited dataset size, the AI weights are incorrect, but the option remains accessible if someone generates a more robust dataset.

### 2. As an API:  
**Run the main_api.py script.**  

- **get health score for a specified platform and package**  
returns marker values, health score and warnings  
`GET http://localhost:5000/score/{platform}/{package}`  
for example: `GET http://localhost:5000/score/npm/pix-diff`  
![score result](images/tool_score_result.PNG)  
**Query parameters:**  
For AI weights:  
    - ai = true  
For different parameter values:  
    - w_marker = changed_value, t1_marker=changed_value, t2_marker = changed_value, otherwise default  
    - e.g. w_created_since=10, t1_contributor_count=5, t2=updated_since=150  
      
- **get parameter information**   
returns marker description, weights and thresholds  
`GET http://localhost:5000/info/`    
![get score](images/info_result.PNG)  


## The readme is not finished, you can reffer to chapter 7 of my master thesis found at https://www.ru.nl/publish/pages/769526/jana_vojnovic.pdf for more information about the tool.

# This tool is not going to be maintained.