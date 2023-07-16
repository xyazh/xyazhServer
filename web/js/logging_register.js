const logging_layer = function(){
    layer.open({
        type: 1,
        resize: false,
        shadeClose: true,
        area: '350px',
        title: '登录',
        content: template("logging_layer_temp",{}),
        success: function(layero, index){
            layero.find('.layui-layer-content').css('overflow', 'visible');
            layui.form.render().on('submit(logging_b)', function(data){
                var r_data = JSON.stringify(data.field);
                $.ajax({
                    url: "/api/logging",
                    type: "post",
                    data: r_data,
                    async: false,
                    success: function(result){
                        var l_data = JSON.parse(result)
                        $.cookie("token",l_data["token"],{});
                        $.cookie("uid",l_data["uid"],{});
                        $.cookie("user_name",l_data["user_name"],{});
                        $.cookie("level",l_data["level"],{});
                        c_token = l_data["token"];
                        c_uid = l_data["uid"];
                        c_user_name = l_data["user_name"];
                        c_level = l_data["level"];
                        $("#user_name").text(l_data["user_name"]);
                        $("#uid").text(l_data["uid"]);
                        $("#logging1").attr("style","display: none;");
                        $("#logging2").attr("style","display: none;");
                        $("#register1").attr("style","display: none;");
                        $("#register2").attr("style","display: none;");
                        layer.close(index);
                    },
                    error: function(xhr,status,error){
                        var m = "错误"
                        switch(xhr.status){
                            case 400:
                                m = "数据字段错误，必填项不能为空";
                                break;
                            case 404:
                                m = "用户不存在";
                                break;
                            case 401:
                                m = "密码错误";
                                break;
                        }
                        layer.msg(m, {icon: 0});
                    }
                });
            });
        }
    });
}
send_mail_timer = 0;
const update_mail_time = function(t){
    try{
        send_mail_timer = t;
        if(t > 0){
            $("#check_mail_button").attr("style","background-color: #bbbbbb;");
            $("#check_mail_button").text("发送邮件(" + t + ")");
            setTimeout("update_mail_time(send_mail_timer-1)",1000);
        }else{
            $("#check_mail_button").attr("style","");
            $("#check_mail_button").text("发送邮件");
        }
    }catch(error){
    }
}
const get_mail_check_code = function(){
    if(send_mail_timer>0){
        return;
    }
    var r_mail = $("#r_mail").val();
    var re_mail = /^\w+([\.\-]\w+)*\@\w+([\.\-]\w+)*\.\w+$/;
    if(!r_mail.match(re_mail)){
        layer.msg("邮箱格式不正确", {icon: 0});
        return;
    }
    $.ajax({
        url: "/api/send_mail_code",
        type: "post",
        data: r_mail,
        async: false,
        success: function(result){
            layer.msg("邮件已发送，未收到请注意检查垃圾箱", {icon: 1});
            update_mail_time(60);
        },
        error: function(xhr,status,error){
            var m="错误"
            switch(xhr.status){
                case 403:
                    m = "重置时间未过";
                    break;
                case 400:
                    m = "邮箱格式不正确";
                    break;
                case 409:
                    m = "邮箱已存在";
                    break;
            }
            layer.msg(m, {icon: 0});
        }
    });
}

const register_layer = function(){
    layer.open({
        type: 1,
        resize: false,
        shadeClose: true,
        area: '350px',
        title: '注册',
        content: template("register_layer_temp",{}),
        success: function(layero, index){
            layero.find('.layui-layer-content').css('overflow', 'visible');
            layui.form.render().on('submit(register_b)', function(data){
                if(data["check_password"] != data["password"]){
                    layer.msg("两次密码不一致", {icon: 0});
                    return;
                }
                var r_data = JSON.stringify(data.field)
                $.ajax({
                    url: "/api/register",
                    type: "post",
                    data: r_data,
                    async: false,
                    success: function(result){
                        var l_data = JSON.parse(result)
                        $.cookie("token",l_data["token"],{});
                        $.cookie("uid",l_data["uid"],{});
                        $.cookie("user_name",l_data["user_name"],{});
                        $.cookie("level",l_data["level"],{});
                        c_token = l_data["token"];
                        c_uid = l_data["uid"];
                        c_user_name = l_data["user_name"];
                        c_level = l_data["level"];
                        $("#user_name").text(l_data["user_name"]);
                        $("#uid").text(l_data["uid"]);
                        $("#logging1").attr("style","display: none;");
                        $("#logging2").attr("style","display: none;");
                        $("#register1").attr("style","display: none;");
                        $("#register2").attr("style","display: none;");
                        layer.close(index);
                    },
                    error: function(xhr,status,error){
                        var m = "错误"
                        switch(xhr.status){
                            case 400:
                                m = "数据字段错误，必填项不能为空";
                                break;
                            case 401:
                                m = "验证码错误";
                                break;
                            case 413:
                                m = "用户名不能长于20个字符";
                                break;
                            case 403:
                                m = "验证码已过期";
                                break;
                            case 409:
                                if(error == "hased username"){
                                    m = "用户名已存在";
                                }else if(error == "hased mail"){
                                    m = "邮箱已存在";
                                }
                                break;
                        }
                        layer.msg(m, {icon: 0});
                    }
                });
            });
        }
    });
}