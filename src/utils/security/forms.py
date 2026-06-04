from wtforms import Form
from wtforms import StringField, PasswordField, BooleanField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo


class LoginForm(Form):
    email = StringField('Email', validators=[
        DataRequired(message='邮箱不能为空'),
        Email(message='邮箱格式不正确')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='密码不能为空'),
        Length(min=6, message='密码长度至少6位')
    ])
    remember_me = BooleanField('Remember Me')


class RegisterForm(Form):
    username = StringField('Username', validators=[
        DataRequired(message='用户名不能为空'),
        Length(min=3, max=20, message='用户名长度必须在3-20个字符之间')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='邮箱不能为空'),
        Email(message='邮箱格式不正确')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='密码不能为空'),
        Length(min=6, message='密码长度至少6位')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message='确认密码不能为空'),
        EqualTo('password', message='两次输入的密码不一致')
    ])
    display_name = StringField('Display Name')
    bio = StringField('Bio')
    location = StringField('Location')
    website = StringField('Website')
    profile_private = BooleanField('Private Profile')
    newsletter = BooleanField('Subscribe to Newsletter')
    marketing_emails = BooleanField('Receive Marketing Emails')
    terms = BooleanField('Terms', validators=[
        DataRequired(message='必须同意服务条款')
    ])
    locale = SelectField('Language Preference', choices=[('zh_CN', '中文'), ('en', 'English')], default='zh_CN')


class ProfileForm(Form):
    username = StringField('Username', validators=[
        DataRequired(message='用户名不能为空'),
        Length(min=4, max=16, message='用户名长度必须在4-16个字符之间')
    ])
    bio = TextAreaField('Bio', validators=[
        Length(max=200, message='个人简介不能超过200个字符')
    ])
    locale = SelectField('Language Preference',
                         choices=[('zh_CN', '中文'), ('en', 'English')],
                         default='zh_CN')
    profile_private = BooleanField('Private Profile')


class ChangePasswordForm(Form):
    current_password = PasswordField('Current Password', validators=[
        DataRequired(message='当前密码不能为空')
    ])
    new_password = PasswordField('New Password', validators=[
        DataRequired(message='新密码不能为空'),
        Length(min=6, message='密码长度至少6位')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(message='确认密码不能为空'),
        EqualTo('new_password', message='两次输入的密码不一致')
    ])

    def validate(self, extra_validators=None):
        # 调用父类的验证方法
        result = super().validate(extra_validators)
        return result


class ConfirmPasswordForm(Form):
    password = PasswordField('Current Password', validators=[
        DataRequired(message='当前密码不能为空')
    ])

    def validate(self, extra_validators=None):
        # 调用父类的验证方法
        result = super().validate(extra_validators)
        return result
