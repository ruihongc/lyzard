let lineNumber = -1;
include("codemirror-5.63.3/lib/codemirror.js");
include("codemirror-5.63.3/mode/python/python.js");
let runAll = false;
let prevLineNumber = 0;
let breakpoints = new Object();

document.getElementById("fileInput").addEventListener("change", function() {
    var fr = new FileReader();
    fr.onload = function() {
        console.log(fr.result);
        myCodeMirror.setValue(fr.result);
    }
    fr.readAsText(this.files[0]);
})

var myCodeMirror = CodeMirror.fromTextArea(document.getElementById("editor"), {
    lineNumbers: true,
    mode: 'python',
    theme: 'monokai',
});
myCodeMirror.setSize(null, "100%");
var myCodeTerminal = CodeMirror.fromTextArea(document.getElementById("terminal"), {
    lineNumbers: true,
    mode: null,
    theme: 'monokai',
    readOnly: 'nocursor'
});
myCodeTerminal.setSize(null, "100%");

var ws = new WebSocket("ws://localhost:8765");
ws.onmessage = function (evt) {
    //dim all unused elements
    var tmpElements3 = document.querySelectorAll(".accessed");
    for (let j = 0; j < tmpElements3.length; j++) tmpElements3[j].classList.remove("accessed");
    var tmpElements4 = document.querySelectorAll(".modified");
    for (let j = 0; j < tmpElements4.length; j++) tmpElements4[j].classList.remove("modified");
    var tmpElements5 = document.querySelectorAll(".new");
    for (let j = 0; j < tmpElements5.length; j++) tmpElements5[j].classList.remove("new");
    var tmpElements6 = document.querySelectorAll(".varItem");
    for (let j = 0; j < tmpElements6.length; j++) tmpElements6[j].classList.add("uselessVar");

    console.log(evt.data);
    var lines = evt.data.split("\n");
    if (evt.data == "Finished") {
        //const tmpButtons = document.getElementsByTagName("BUTTON");
        //for (let k = 0; k < tmpButtons.length; k++) tmpButtons[k].classList.add("d-none");
        stopRunAll();
        selReset();
    }
    else {
        for (let j = 0; j < lines.length; j++) lines[j] = lines[j].trim();

        //output on terminal
        let i = 0;
        while (lines[i] != "------") {
            if (lines[i].startsWith("input:")) {
                displayTerminal(lines[i].substring(7));
                let userInput = pyInput(lines[i]);
                displayTerminal(userInput, true);
                ws.send(userInput);
                return 0;
            }
            else if (lines[i] != "") displayTerminal(lines[i]);
            i += 1;
        }
        i += 1;

        //variables modified
        for (let j = 0; j < lines[i].length; j++) {
            let tmpVarName = "";
            let tmpVarVal = "";
            let tmpIndex = [];
            let tmpMode = "";

            //get variable name
            while(lines[i][j] != " ") {
                if (lines[i][j] == "[") break;
                tmpVarName += lines[i][j];
                j++;
            }

            //if is element in array i.e. a[0], get variable index(es)
            if (lines[i][j] == "[") {
                j++;
                while(lines[i][j] != " ") {
                    if (lines[i][j] != "]" && lines[i][j] != "[") tmpIndex.push(lines[i][j]);
                    j++;
                }
            }
            j++;

            //get raw displayed value
            //signal, weird things to arrays
            if (lines[i][j] == "(" && lines[i].length >= j+5) {
                for (let k = 0; k < 5; k++) {
                    tmpMode += lines[i][j];
                    j++;
                }
                if (!(tmpMode == "(INS)"||tmpMode == "(DEL)"||tmpMode == "(CLR)")) tmpVarVal += tmpMode;
            }
            //if array
            if (lines[i][j] == "[" && tmpVarVal == "") {
                let openBracKount = 0;
                let closeBracKount = 0;
                while(openBracKount != closeBracKount||openBracKount === 0) {
                    if (lines[i][j] == "[") openBracKount++;
                    else if (lines[i][j] == "]") closeBracKount++;
                    tmpVarVal += lines[i][j];
                    j++;
                }
                tmpVarVal = JSON.parse(tmpVarVal);
            }
            //if variable
            else {
                while(lines[i][j] != ",") {
                    tmpVarVal += lines[i][j];
                    j++;
                }
            }
            j++;

            //create/build variable
            if (!document.getElementById(htmlVarId(tmpVarName))) {
                buildVar(tmpVarName, tmpVarVal);
            }
            else {
                if (tmpMode == "(DEL)") delArr(tmpVarName, tmpIndex);
                else if (tmpMode == "(INS)") insArr(tmpVarName, tmpVarVal, tmpIndex);
                else {
                    if (tmpMode == "(CLR)") tmpVarVal = "";
                    if (Array.isArray(tmpVarVal) && tmpIndex.length == 0) modVar(tmpVarName, tmpVarVal);
                    else modVar(tmpVarName, tmpVarVal, tmpIndex);
                }
            }
        }
        i += 1;

        //variables accessed
        var accVars = lines[i].split(" ");
        for (let j = 0; j < accVars.length; j++) {
            accVars[j] = accVars[j].trim();
            if (!accVars[j]) continue;
            //whole variable/array
            if (document.getElementById(htmlVarId(accVars[j]))) {
                highVar(accVars[j], "accessed");
            }
            else if (!accVars[j].includes("[")) continue;
            //array component
            else {
                let tmpVarName = "";
                let tmpIndex = [];
                let k = 0;
                accVars[j] += " ";
                while(accVars[j][k] != "[") {
                    tmpVarName += accVars[j][k];
                    k++;
                }
                while(accVars[j][k] != " ") {
                    k++;
                    let tmpTmpIndex = "";
                    while(accVars[j][k] != "]") {
                        tmpTmpIndex += accVars[j][k];
                        k++;
                    }
                    tmpIndex.push(tmpTmpIndex);
                    k++;
                }
                if (tmpIndex.length == 1) tmpIndex = tmpIndex[0];
                highVar(tmpVarName, "accessed", tmpIndex);
            }
        }
        i++;

        //breakpoint
        if (lines[i] != "-1") {
            breakpoints[parseInt(lines[i])] = lineNumber;
        }
        i++;

        //line to jump to
        if (lines[i] != "-1") {
            lineNumber = breakpoints[parseInt(lines[i])] - 1;
        }

        if (runAll) {
            if (document.getElementById("runAllDelay").value) {
                setTimeout(function() {
                    processNextLine()
                }, parseInt(document.getElementById("runAllDelay").value));
            }
            else processNextLine();
        }
    }
};

function include(file) {
    var script  = document.createElement('script');
    script.src  = file;
    script.type = 'text/javascript';
    script.defer = true;
    document.getElementsByTagName('head').item(0).appendChild(script);
}

function htmlVarId(varName) {
    return 'varVarVar' + varName;
}

function displayTerminal(lineContent, changePrefix = false) {
    let tmpCount = myCodeTerminal.lineCount() + 1;
    let lineStarter = ">>> ";
    if (changePrefix) lineStarter = "<<< ";
    myCodeTerminal.replaceRange(lineStarter+lineContent+"\n", {line: tmpCount, ch: 0});
    return 0;
}

function pyInput(inputStr) {
    return window.prompt(inputStr.substring(7), "Input...");
}

function selNextLine() {
    var tmpButton = document.getElementById("mainButton");

    //hide delay input
    document.getElementById("runAllDelay").classList.add("d-none");

    //colour
    tmpButton.children[0].setAttribute("style", "width: 120px; color: black; background-color: #F9D1D1; border-color: #F9D1D1;");
    tmpButton.children[1].setAttribute("style", "color: black; background-color: #F9D1D1; border-color: #F9D1D1;");

    //content and action
    tmpButton.children[0].innerHTML = tmpButton.children[2].children[0].innerHTML;
    tmpButton.children[0].setAttribute("onclick", "processNextLine()");

    //set blue highlight
    tmpButton.children[2].children[0].classList.add("active");
    tmpButton.children[2].children[1].classList.remove("active");
    tmpButton.children[2].children[2].classList.remove("active");
    return 0;
}

function selAllLine() {
    var tmpButton = document.getElementById("mainButton");

    //show delay input
    document.getElementById("runAllDelay").classList.remove("d-none");

    //colour
    tmpButton.children[0].setAttribute("style", "width: 120px; color: black; background-color: #FFA4B6; border-color: #FFA4B6;");
    tmpButton.children[1].setAttribute("style", "color: black; background-color: #FFA4B6; border-color: #FFA4B6;");

    //content and action
    tmpButton.children[0].innerHTML = tmpButton.children[2].children[1].innerHTML;
    tmpButton.children[0].setAttribute("onclick", "runAllLines()");

    //set blue highlight
    tmpButton.children[2].children[0].classList.remove("active");
    tmpButton.children[2].children[1].classList.add("active");
    tmpButton.children[2].children[2].classList.remove("active");
    return 0;
}

function selReset() {
    var tmpButton = document.getElementById("mainButton");

    //hide delay input
    document.getElementById("runAllDelay").classList.add("d-none");

    //colour
    tmpButton.children[0].setAttribute("style", "width: 120px; color: black; background-color: orange; border-color: orange;");
    tmpButton.children[1].setAttribute("style", "color: black; background-color: orange; border-color: orange;");

    //content and action
    tmpButton.children[0].innerHTML = tmpButton.children[2].children[2].innerHTML;
    tmpButton.children[0].setAttribute("onclick", "resetFunc()");

    //set blue highlight
    tmpButton.children[2].children[0].classList.remove("active");
    tmpButton.children[2].children[1].classList.remove("active");
    tmpButton.children[2].children[2].classList.add("active");
    return 0;
}

function processNextLine() {
    myCodeMirror.save();
    myCodeMirror.removeLineClass(prevLineNumber, "background", "highLine");
    lineNumber += 1;
    myCodeMirror.addLineClass(lineNumber, "background", "highLine");
    var lines = document.getElementById("editor").value.split("\n");
    if (lineNumber >= lines.length) {
        console.log("<===7");
        ws.send("<===7");
    }
    else {
        console.log(lines[lineNumber]);
        ws.send(lines[lineNumber]);
    }
    prevLineNumber = lineNumber;
    return 0;
}

function runAllLines() {
    var tmpButton = document.getElementById("mainButton");
    tmpButton.children[1].disabled = true;

    //colour
    tmpButton.children[0].setAttribute("style", "background-color: red; border-color: red;");
    tmpButton.children[1].setAttribute("style", "background-color: red; border-color: red;");

    //content and action
    tmpButton.children[0].innerHTML = "Stop Running";
    tmpButton.children[0].setAttribute("onclick", "stopRunAll()");

    runAll = true;
    processNextLine();
    return 0;
}

function stopRunAll() {
    runAll = false;
    var tmpButton = document.getElementById("mainButton");
    tmpButton.children[1].disabled = false;
    selAllLine();
    return 0;
}

function openFile() {
    document.getElementById("fileInput").click();
    return 0;
}

function resetFunc() {
    if (runAll) stopRunAll();
    selNextLine();
    myCodeMirror.removeLineClass(prevLineNumber, "background", "highLine");
    lineNumber = -1;
    document.getElementById("varBox").innerHTML = "";
    myCodeTerminal.setValue("");
    myCodeTerminal.clearHistory();
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.open("GET", "http://localhost:8080/reset", false); // false for synchronous request
    xmlHttp.send(null);
    console.log(xmlHttp.responseText);
    return xmlHttp.responseText;
}

function buildVal(content) {
    return '<div class="align-items-center varVal d-flex flex-row">'+content+'</div>';
}

function buildIndex(ind) {
    return '<div class="arrIndex">'+ind+'</div>';
}

function buildArr(varArr, ind) {
    const spanTag = '<span class="w-auto varItem m-2 d-flex flex-column">';
    if (!Array.isArray(varArr)) return spanTag+buildVal(varArr)+buildIndex(ind)+'</span>';
    var contentHTML = "";
    for (let i = 0; i < varArr.length; i++) contentHTML += buildArr(varArr[i], i);
    return spanTag+buildVal(contentHTML)+buildIndex(ind)+'</span>';
}

function buildName(varName) {
    return '<span class="varName">'+varName+'</span>';
}

function buildVarInnards(varArr) {
    let contentHTML = "";
    if (!Array.isArray(varArr)) contentHTML += '<span class="w-auto varItem m-2 d-flex flex-column">'+buildVal(varArr)+'</span>';
    else {
        for (let i = 0; i < varArr.length; i++) {
            contentHTML += buildArr(varArr[i], i);
        }
    }
    return contentHTML;
}

function buildVar(varName, varArr) {
    const tmpId = htmlVarId(varName);
    let contentHTML = buildName(varName)+buildVarInnards(varArr);
    const divTag = '<div id="'+tmpId+'" class="bigVarHolder align-items-center mb-3 varItem d-flex flex-row">';
    document.getElementById("varBox").innerHTML += divTag + contentHTML + '</div>';
    highVar(varName);
    return divTag + contentHTML + '</div>';
}

function highVar(varName, highType = 'new', varIndex = 'all') {
    const tmpVarId = htmlVarId(varName);

    //remove overall hiding
    document.getElementById(tmpVarId).classList.remove('uselessVar');

    //children[0] to get box within span
    if (varIndex == "all") {
        var tmpElement = document.getElementById(tmpVarId).querySelectorAll('.varItem');
        for (let i = 0; i < tmpElement.length; i++) {
            tmpElement[i].classList.remove('uselessVar');
            tmpElement[i].children[0].classList.add(highType);
        }
    }
    else {
        var tmpElement = arrFinder(varName, varIndex);
        tmpElement.classList.remove('uselessVar');
        tmpElement.children[0].classList.add(highType);

        //highlight all parent elements
        for (let i = 1; i < varIndex.length; i++) {
            if (!tmpElement.parentElement.parentElement) break;
            if (highType == "new") highType = "modified";
            tmpElement = tmpElement.parentElement.parentElement;
            tmpElement.classList.remove('uselessVar');
            tmpElement.children[0].classList.add(highType);
        }
    }
    return 0;
}

function modVar(varName, varArr, varIndex = 'all') {
    const tmpVarId = htmlVarId(varName);

    //children[0] to get box within span
    if (varIndex == "all") {
        var contentHTML = buildVarInnards(varArr);
        while (document.getElementById(tmpVarId).children.length > 1) {
            document.getElementById(tmpVarId).removeChild(document.getElementById(tmpVarId).lastChild);
        }
        document.getElementById(tmpVarId).innerHTML += contentHTML;
        highVar(varName, 'modified');
    }
    else if (varIndex.length == 0) {
        document.getElementById(tmpVarId).children[1].children[0].innerHTML = varArr;
        highVar(varName, 'modified');
    }
    else {
        var tmpElement = arrFinder(varName, varIndex);
        if (Array.isArray(varArr)) tmpElement.children[0].innerHTML = buildVarInnards(varArr);
        else tmpElement.children[0].innerHTML = varArr;
        highVar(varName, 'modified', varIndex);
    }
    return 0;
}

function delArr(varName, varIndex) {
    var tmpElement = arrFinder(varName, varIndex);
    var tmpParent = tmpElement.parentElement;
    //get index
    var immediateIndex = parseInt(tmpElement.children[1].innerHTML);
    tmpParent.removeChild(tmpElement);

    //adjust index of elements after
    for (let i = 0; i < tmpParent.children.length; i++) {
        if (tmpParent.children[i].children.length > 0) {
            var tmpIndex = parseInt(tmpParent.children[i].children[1].innerHTML);
            if (tmpIndex > immediateIndex) tmpParent.children[i].children[1].innerHTML = tmpIndex - 1;
        }
    }

    varIndex.pop();
    if (Array.isArray(varIndex)) highVar(varName, "modified", varIndex);
    else highVar(varName, "modified");
    return 0;
}

function insArr(varName, varArr, varIndex) {
    var emptiness = false;
    var tmp;
    if (Array.isArray(varIndex)) {
        varIndex[varIndex.length-1]--;
        if (varIndex[varIndex.length-1] == -1) emptiness = true;
        if (varIndex.length == 1) varIndex = varIndex[0];
    }
    else {
        varIndex--;
        if (varIndex == -1) emptiness = true;
    }
    if (emptiness) {
        var tmpElement;
        if (Array.isArray(varIndex)) {
            tmp = varIndex.pop();
            tmpElement = arrFinder(varName, varIndex);
            varIndex.push(tmp);
            tmpElement.children[0].insertAdjacentHTML("afterbegin", buildArr(varArr, 0));
        }
        else {
            tmpElement = document.getElementById(htmlVarId(varName));
            tmpElement.children[0].insertAdjacentHTML("afterend", buildArr(varArr, 0));
        }
    }
    else {
        var tmpElement = arrFinder(varName, varIndex);
        var tmpParent = tmpElement.parentElement;
        //get index
        var immediateIndex = parseInt(tmpElement.children[1].innerHTML);
        tmpElement.insertAdjacentHTML("afterend", buildArr(varArr, immediateIndex+1));

        //adjust index for elements after
        let prevIndex = -1;
        for (let i = 0; i < tmpParent.children.length; i++) {
            if (tmpParent.children[i].children.length > 1) {
                var tmpIndex = parseInt(tmpParent.children[i].children[1].innerHTML);
                if (tmpIndex != prevIndex+1) tmpParent.children[i].children[1].innerHTML = tmpIndex + 1;
                prevIndex = parseInt(tmpParent.children[i].children[1].innerHTML);
            }
        }
    }
    if (Array.isArray(varIndex)) varIndex[varIndex.length-1]++;
    else varIndex++;
    highVar(varName, "new", varIndex);
    return 0;
}

function arrFinder(varName, varIndex) {
    const tmpVarId = htmlVarId(varName);
    if (!Array.isArray(varIndex)) {
        if (parseInt(varIndex) < 0||parseInt(varIndex) > document.getElementById(tmpVarId).children.length-2) return document.getElementById('placeholderDiv');
        return document.getElementById(tmpVarId).children[parseInt(varIndex)+1];
    }
    if (parseInt(varIndex[0]) < 0||parseInt(varIndex[0]) > document.getElementById(tmpVarId).children.length-2) return document.getElementById('placeholderDiv');
    var tmpElement = document.getElementById(tmpVarId).children[parseInt(varIndex[0])+1];
    for (let i = 1; i < varIndex.length; i++) {
        if (parseInt(varIndex[i]) < 0||parseInt(varIndex[i]) > tmpElement.children[0].children.length-1) return document.getElementById('placeholderDiv');
        tmpElement = tmpElement.children[0].children[parseInt(varIndex[i])];
    }
    return tmpElement;
}

/*<div class="row flex-grow-1 overflow-scroll d-flex flex-column" id="varBox">
    <div id="varVarVarx" class="bigVarHolder align-items-center mb-3 varItem d-flex flex-row">
        <span class="varName">
            x
        </span>
        <span class="w-auto varItem m-2 d-flex flex-column">
            <div class="varVal modified d-flex flex-row">
                <span class="w-auto varItem m-2 d-flex flex-column">
                    <div class="varVal modified">
                        3
                    </div>
                    <div class="arrIndex">
                        0
                    </div>
                </span>
                <span class="w-auto varItem m-2 d-flex flex-column">
                    <div class="varVal modified">
                        4
                    </div>
                    <div class="arrIndex">
                        1
                    </div>
                </span>
            </div>
            <div class="arrIndex">
                0
            </div>
        </span>
        <span class="w-auto varItem m-2 d-flex flex-column">
            <div class="varVal modified d-flex flex-row">
                5
            </div>
            <div class="arrIndex">
                1
            </div>
        </span>
    </div>
    <div id="varVarVarx" class="bigVarHolder align-items-center mb-3 varItem d-flex">
        <span class="varName">
            y
        </span>
        <span class="w-auto varItem m-2 d-flex flex-column">
            <div class="varVal modified d-flex flex-row">
                abc
            </div>
        </span>
    </div>
</div>*/