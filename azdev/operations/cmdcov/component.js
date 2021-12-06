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
    if (a==='N/A'){
        a = -1
    } else if (a===''){
        a = 100
    } else {
        a = parseFloat(a.substr(0,a.length-1))
    }
    if (b==='N/A'){
        b = -1
    } else if (b===''){
        b = 100
    } else {
        b = parseFloat(b.substr(0,b.length-1))
    }
    if (a < b) {
        return -1;
    }
    if (a > b) {
        return 1;
    }
}
function sortTextDesc(a, b)
{
    if (a==='N/A'){
        a = -1
    } else if (a===''){
        a = 100
    }  else {
        a = parseFloat(a.substr(0,a.length-1))
    }
    if (b==='N/A'){
        b = -1
    } else if (b===''){
        b = 100
    }  else {
        b = parseFloat(b.substr(0,b.length-1))
    }
    if (a < b) {
        return 1;
    }
    if (a > b) {
        return -1;
    }
}

function SortTable(obj){
    var column=obj.id
    var td0s=document.getElementsByName("td0");
    var td1s=document.getElementsByName("td1");
    var td2s=document.getElementsByName("td2");
    var td3s=document.getElementsByName("td3");
    var td4s=document.getElementsByName("td4");
    var td5s=document.getElementsByName("td5");
    var tdArray0=[];
    var tdArray1=[];
    var tdArray2=[];
    var tdArray3=[];
    var tdArray4=[];
    var tdArray5=[];
    for(var i=0;i<td0s.length;i++){
        tdArray0.push(td0s[i].innerHTML);
    }
    for(var i=0;i<td1s.length;i++){
        tdArray1.push(td1s[i].innerHTML);
    }
    for(var i=0;i<td2s.length;i++){
        tdArray2.push(td2s[i].innerHTML);
    }
    for(var i=0;i<td3s.length;i++){
        tdArray3.push(td3s[i].innerHTML);
    }
    for(var i=0;i<td4s.length;i++){
        tdArray4.push(td4s[i].innerHTML);
    }
    for(var i=0;i<td5s.length;i++){
        tdArray5.push(td5s[i].innerHTML);
    }
    var tds=document.getElementsByName("td"+obj.id.substr(2,1));
    var columnArray=[];
    for(var i=0;i<tds.length;i++){
        if(column==='th1' || column==='th2'){
            columnArray.push(parseInt(tds[i].innerHTML));
        }else if(column==='th0' || column==='th5'){
            columnArray.push(tds[i].innerHTML);
        }else{
            columnArray.push(tds[i].innerText);
        }
    }
    var orginArray=[];
    for(var i=0;i<columnArray.length;i++){
        orginArray.push(columnArray[i]);
    }
    var newArray = columnArray.slice(1,)
    if(obj.className=="as"){
        if(column==='th1' || column==='th2'){
            newArray.sort(sortNumberAS);
        }else if(column==='th0' || column==='th5'){
            newArray.sort(sortStrAS);
        }else{
            newArray.sort(sortTextAS);
        }
        obj.className="desc";
    }else{
        if(column==='th1' || column==='th2'){
            newArray.sort(sortNumberDesc);
        }else if(column==='th0' || column==='th5'){
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
                document.getElementsByName("td0")[i].innerHTML=tdArray0[j];
                document.getElementsByName("td1")[i].innerHTML=tdArray1[j];
                document.getElementsByName("td2")[i].innerHTML=tdArray2[j];
                document.getElementsByName("td3")[i].innerHTML=tdArray3[j];
                document.getElementsByName("td4")[i].innerHTML=tdArray4[j];
                document.getElementsByName("td5")[i].innerHTML=tdArray5[j];
                orginArray[j]=null;
                break;
            }
        }
    }
}
