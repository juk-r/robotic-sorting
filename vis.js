function update(time){
    for (let i = 0; i < robots.length; i++) {
        if (data[time][i][0] == 0) continue;
        x = data[time][i][2]*MOVE + CELL_SIZE/2;
        y = data[time][i][1]*MOVE + CELL_SIZE/2;
        if (data[time][i][3] == ((rotations[i]+1)%4+4)%4){
            rotations[i] += 1;
        }
        else if (data[time][i][3] == ((rotations[i]+3)%4+4)%4){
            rotations[i] -= 1;
        }
        else if (data[time][i][3] == ((rotations[i]+2)%4+4)%4){
            rotations[i] += 2;
        }
        robots[i].setAttribute("style", "transition: "+SPEED*data[time][i][0]+"s")
        robots[i].getElementsByClassName("mail")[0].setAttribute("style", "transition: "+SPEED*data[time][i][0]+"s")
        robots[i].setAttribute("transform", "translate("+x+","+y+")\
        rotate(" + (-90*rotations[i]) + ")");
        if (data[time][i][4]){
            robots[i].setAttribute("mail", "true");
        }
        else{
            robots[i].setAttribute("mail", "false");
        }
    }
}
robots = [];
rotations = [];
for (let i = 0; i < data[0].length; i++) {
    robots.push(document.getElementById("r"+i));
    rotations.push(data[0][i][2]);
}
for (let i = 0; i < data.length; i++) {
    setTimeout(update, i*1000*SPEED, i);
}