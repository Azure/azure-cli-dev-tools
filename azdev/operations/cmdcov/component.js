var tag=1;
function sortNumberAS(a, b)
{
    return a - b
}
function sortNumberDesc(a, b)
{
    return b - a
}
function sortStrAS(a, b)
{
    x = a.toUpperCase();
    y = b.toUpperCase();
    if (x < y) {
        return -1;
    }
    if (x > y) {
        return 1;
    }
}
function sortStrDesc(a, b)
{
    x = a.toUpperCase();
    y = b.toUpperCase();
    if (x < y) {
        return 1;
    }
    if (x > y) {
        return -1;
    }
}
function sortTextAS(a, b)
{
    if (a === 'Not applicable' || a === 'N/A') {
        a = -1;
    } else if (a === '') {
        a = 100;
    } else {
        a = parseFloat(a.substr(0, a.length - 1));
    }
    if (b === 'Not applicable' || b === 'N/A') {
        b = -1;
    } else if (b === '') {
        b = 100;
    } else {
        b = parseFloat(b.substr(0, b.length - 1));
    }
    if (a < b) {
        return -1;
    }
    if (a > b) {
        return 1;
    }
    return 0; // In case a and b are equal
}
function sortTextDesc(a, b)
{
    if (a === 'Not applicable' || a === 'N/A') {
        a = -1;
    } else if (a === '') {
        a = 100;
    } else {
        a = parseFloat(a.substr(0, a.length - 1));
    }
    if (b === 'Not applicable' || b === 'N/A') {
        b = -1;
    } else if (b === '') {
        b = 100;
    } else {
        b = parseFloat(b.substr(0, b.length - 1));
    }
    if (a < b) {
        return 1;
    }
    if (a > b) {
        return -1;
    }
    return 0; // In case a and b are equal
}


function SortTable(obj){
    var column=obj.id
    var tdModule=document.getElementsByName("td-module");
    var tdTested=document.getElementsByName("td-tested");
    var tdUntested=document.getElementsByName("td-untested");
    var tdPercentage=document.getElementsByName("td-percentage");
    var tdDetail=document.getElementsByClassName("detail")
    var tdReport=document.getElementsByName("td-report");
    var tdModuleArray=[];
    var tdTestedArray=[];
    var tdUntestedArray=[];
    var tdPercentageArray=[];
    var tdReportArray=[];
    for(var i=0;i<tdModule.length;i++){
        tdModuleArray.push(tdModule[i].innerHTML);
    }
    for(var i=0;i<tdTested.length;i++){
        tdTestedArray.push(tdTested[i].innerHTML);
    }
    for(var i=0;i<tdUntested.length;i++){
        tdUntestedArray.push(tdUntested[i].innerHTML);
    }
    for(var i=0;i<tdPercentage.length;i++){
        tdPercentageArray.push(tdPercentage[i].innerHTML);
    }
    for(var i=0;i<tdReport.length;i++){
        tdReportArray.push(tdReport[i].innerHTML);
    }
    var columnArray=[];
    for(var i=0;i<tdModule.length;i++){
        if(column==='th-module'){
            columnArray.push(tdModule[i].innerHTML);
        }else if(column==='th-tested'){
            columnArray.push(parseInt(tdTested[i].innerHTML));
        }else if(column==='th-untested'){
            columnArray.push(parseInt(tdUntested[i].innerHTML));
        }else if(column==='th-percentage'){
            columnArray.push(tdDetail[i].innerHTML)
        }else if(column==='th-report'){
            columnArray.push(tdReport[i].innerHTML);
        }
    }
    var orginArray=[];
    for(var i=0;i<columnArray.length;i++){
        orginArray.push(columnArray[i]);
    }
    var newArray = columnArray.slice(1,)
    if(obj.className=="as"){
        if(column==='th-tested' || column==='th-untested'){
            newArray.sort(sortNumberAS);
        }else if(column==='th-module' || column==='th-report'){
            newArray.sort(sortStrAS);
        }else{
            newArray.sort(sortTextAS);
        }
        obj.className="desc";
    }else{
        if(column==='th-tested' || column==='th-untested'){
            newArray.sort(sortNumberDesc);
        }else if(column==='th-module' || column==='th-report'){
            newArray.sort(sortStrDesc);
        }else{
            newArray.sort(sortTextDesc);
        }
        obj.className="as";
    }
    columnArray = $.merge([columnArray[0]], newArray);
    for(var i=1;i<columnArray.length;i++){
        for(var j=1;j<orginArray.length;j++){
            if(orginArray[j]==columnArray[i]){
                document.getElementsByName("td-module")[i].innerHTML=tdModuleArray[j];
                document.getElementsByName("td-tested")[i].innerHTML=tdTestedArray[j];
                document.getElementsByName("td-untested")[i].innerHTML=tdUntestedArray[j];
                document.getElementsByName("td-percentage")[i].innerHTML=tdPercentageArray[j];
                document.getElementsByName("td-report")[i].innerHTML=tdReportArray[j];
                orginArray[j]=null;
                break;
            }
        }
    }
}
