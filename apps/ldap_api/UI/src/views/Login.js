import React, {Component} from 'react';
import PropTypes from 'prop-types';
import Avatar from '@material-ui/core/Avatar';
import Button from '@material-ui/core/Button';
import CssBaseline from '@material-ui/core/CssBaseline';
import FormControl from '@material-ui/core/FormControl';
import FormControlLabel from '@material-ui/core/FormControlLabel';
import Checkbox from '@material-ui/core/Checkbox';
import Input from '@material-ui/core/Input';
import InputLabel from '@material-ui/core/InputLabel';
import LockOutlinedIcon from '@material-ui/icons/LockOutlined';
import Paper from '@material-ui/core/Paper';
import Typography from '@material-ui/core/Typography';
import withStyles from '@material-ui/core/styles/withStyles';
import {connect} from 'react-redux'
import {Link} from 'react-router-dom';
import {userActions} from '../actions/authActions'

const styles = theme => ({
  main: {
    width: 'auto',
    display: 'block', // Fix IE 11 issue.
    marginLeft: theme.spacing.unit * 3,
    marginRight: theme.spacing.unit * 3,
    [theme.breakpoints.up(400 + theme.spacing.unit * 3 * 2)]: {
      width: 400,
      marginLeft: 'auto',
      marginRight: 'auto',
    },
  },
  paper: {
    marginTop: theme.spacing.unit * 8,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    padding: `${theme.spacing.unit * 2}px ${theme.spacing.unit * 3}px ${theme.spacing.unit * 3}px`,
  },
  avatar: {
    margin: theme.spacing.unit,
    backgroundColor: theme.palette.secondary.main,
  },
  form: {
    width: '100%', // Fix IE 11 issue.
    marginTop: theme.spacing.unit,
  },
  submit: {
    marginTop: theme.spacing.unit * 3,
  },
});

class Login extends Component{
  
  constructor(props){
    super(props);
    this.state = {
      email : '',
      password: '',
      loading: false
    };
  }
  
  handleInputChange = (event) => {
    const { value, name } = event.target;
    this.setState({
      [name]: value
    });
  }
  
  onSubmit = (event) => {
    event.preventDefault();
    this.props.login({username: this.state.username, password: this.state.password})
  }

  render(){
    const { classes } = this.props;

    return (
      <main className={classes.main}>
        <CssBaseline />
        <Paper className={classes.paper}>
          <Avatar className={classes.avatar}>
            <LockOutlinedIcon />
          </Avatar>
          <Typography component="h1" variant="h5">
            Iniciar Sesión en Directorio
          </Typography>
          <form className={classes.form} onSubmit={this.onSubmit}>
            <FormControl margin="normal" required fullWidth>
              <InputLabel htmlFor="username">Correo</InputLabel>
              <Input id="username" name="username" autoComplete="username" type="email" autoFocus onChange={this.handleInputChange} />
            </FormControl>
            <FormControl margin="normal" required fullWidth>
              <InputLabel htmlFor="password">Contraseña</InputLabel>
              <Input name="password" type="password" id="password" autoComplete="current-password" onChange={this.handleInputChange} />
            </FormControl>
            <FormControlLabel
              control={<Checkbox value="remember" color="primary" />}
              label="Recuérdame"
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              color="primary"
              disabled={this.props.loading}
              className={classes.submit}
            >
              Iniciar
            </Button>
            <Typography component="p" style={{marginTop: 15}}>
              <Link to="/p/recuperar">
                ¿Olvidaste tu contraseña?
              </Link>
            </Typography>
            <Typography component="p" style={{marginTop: 15}}>
              <Link to="/p/preguntasdeseguridad">
                Gestiona tus preguntas de seguridad
              </Link>
            </Typography>
            <Typography component="p" style={{marginTop: 15}}>
              <Link to="/p/cambiar">
                Cambiar contraseña
              </Link>
            </Typography>
            <Typography component="p" style={{marginTop: 15}}>
              <Link to="/p/agregarestudiante">
                Agregar Trabajador
              </Link>
            </Typography>
            <Typography component="p" style={{marginTop: 15}}>
              <Link to="/p/agregartrabajador">
                Agregar Estudiante
              </Link>
            </Typography>
          </form>
        </Paper>
      </main>
    );
  }
}

Login.propTypes = {
  classes: PropTypes.object.isRequired,
};

const mapStateToProps = (state) => ({
  loading: state.login.loggingIn
});

export default connect(mapStateToProps, {login: userActions.login})(withStyles(styles)(Login));