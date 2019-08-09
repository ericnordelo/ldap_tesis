import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { withStyles } from '@material-ui/core/styles';
import CssBaseline from '@material-ui/core/CssBaseline';
import Toolbar from '@material-ui/core/Toolbar';
import Paper from '@material-ui/core/Paper';
import Typography from '@material-ui/core/Typography';
import {Link} from 'react-router-dom';
import Grid from '@material-ui/core/Grid';
import Button from '@material-ui/core/Button';
import TextField from '@material-ui/core/TextField';
import {passwordActions} from '../actions/passwordActions'
import {connect} from 'react-redux'
import {sections} from './_sections'
import {footer} from './_footer'
import config from '../config';

const styles = theme => ({
  layout: {
    width: 'auto',
    marginLeft: theme.spacing.unit * 3,
    marginRight: theme.spacing.unit * 3,
    [theme.breakpoints.up(1100 + theme.spacing.unit * 3 * 2)]: {
      width: 1100,
      marginLeft: 'auto',
      marginRight: 'auto',
    },
  },
  captionLink:{
    color: "black",
  },
  toolbarMain: {
    borderBottom: `1px solid ${theme.palette.grey[300]}`,
  },
  toolbarTitle: {
    flex: 1,
  },
  toolbarSecondary: {
    justifyContent: 'space-between',
  },
  mainFeaturedPost: {
    backgroundColor: theme.palette.grey[800],
    color: theme.palette.common.white,
    marginBottom: theme.spacing.unit * 4,
  },
  mainFeaturedPostContent: {
    padding: `${theme.spacing.unit * 6}px`,
    [theme.breakpoints.up('md')]: {
      paddingRight: 0,
    },
  },
  mainGrid: {
    marginTop: theme.spacing.unit * 3,
  },
  card: {
    display: 'flex',
  },
  cardDetails: {
    flex: 1,
  },
  cardMedia: {
    width: 160,
  },
  markdown: {
    padding: `${theme.spacing.unit * 3}px 0`,
  },
  sidebarAboutBox: {
    padding: theme.spacing.unit * 2,
    backgroundColor: theme.palette.grey[200],
  },
  sidebarSection: {
    marginTop: theme.spacing.unit * 3,
  },
  footer: {
    backgroundColor: theme.palette.background.paper,
    marginTop: theme.spacing.unit * 8,
    padding: `${theme.spacing.unit * 6}px 0`,
  },
  submit: {
    marginTop: 15
  }
});

class RecoverPassword extends Component{

  constructor(props){
    super(props);
    this.state = {
      email: '',
      pregunta1: '',
      pregunta2: '',
      respuesta1: '',
      respuesta2: '',
      password: '',
      password2: '',
      loading: false
    };
  }

  handleChange = name => event => {
    this.setState({ [name]: event.target.value });
  };

  getQuestions = (event) => {
    event.preventDefault();

    if(this.state.email === ''){
      alert('El correo no puede estar en blanco.');
      return;
    }

    this.props.start_loading();

    fetch(config.api_address + '/p/preguntasdeseguridad?email='+this.state.email, {
        credentials: "include",
        method: 'GET'
    })
    .then(res => res.json())
    .then(data => {
        if(data.error === 'No tiene preguntas de seguridad'){
          alert('No tiene preguntas de seguridad agregadas.');
        } else if(data.error){
          alert('Su correo no existe en el directorio.');
        }
        else{
          this.setState({pregunta1: data.preguntas[0], pregunta2: data.preguntas[1]})
        }
        this.props.end_loading();
    })
    .catch(err => {
        this.props.end_loading();
        console.error(err);
        alert('Ha ocurrido un error al chequear su corro.');
    });
  }

  setQuestions = (event) => {
    event.preventDefault();

    if(this.state.password === '' || this.state.email === ''){
      alert('Las credenciales son requeridas.');
      return;
    }

    if(this.state.pregunta1 === '' || this.state.pregunta2 === '' || this.state.respuesta1 === '' || this.state.respuesta2 === ''){
      alert('Las preguntas y respuestas no pueden estar en blanco.');
      return;
    }

    this.props.start_loading();

    fetch(config.api_address + '/p/preguntasdeseguridad', {
        credentials: "include",
        method: 'PUT',
        body: JSON.stringify({
          email: this.state.email,
          password: this.state.password,
          questions: [this.state.pregunta1, this.state.pregunta2],
          answers: [this.state.respuesta1, this.state.respuesta2],
        }),
        headers: {
          'Content-Type': 'application/json'
        }
    })
    .then(res => res.json())
    .then(data => {
        if(data.error){
          alert('Sus credenciales son incorrectas.');
        }else{
          alert('Preguntas y respuestas de seguridad actualizadas satisfactoriamente.');
        }
        this.props.end_loading();
    })
    .catch(err => {
        this.props.end_loading();
        console.error(err);
        alert('Sus credenciales son incorrectas.');
    });
  }

  render(){
    const {classes} = this.props;
    let showForm2 = false;
    if (this.state.pregunta1.length > 0) {
      showForm2 = true;
    }
    return (
      <React.Fragment>
        <CssBaseline />
        <div className={classes.layout}>
          <Toolbar className={classes.toolbarMain}>
            <Typography
              component="h2"
              variant="h5"
              color="inherit"
              align="center"
              noWrap
              className={classes.toolbarTitle}
            >
              Directorio Único UH
            </Typography>

          </Toolbar>
          <Toolbar variant="dense" className={classes.toolbarSecondary}>
            {sections.map(section => (
              <Link to={section[1]}className={classes.captionLink}>
                <Typography color="inherit" noWrap key={section[0]}>
                  {section[0]}
                </Typography>
              </Link>
            ))}
          </Toolbar>
          <main>
            {/* Main featured post */}
            <Paper className={classes.mainFeaturedPost}>
              <Grid container>
                <Grid item md={6}>
                  <div className={classes.mainFeaturedPostContent}>
                    <Typography component="h1" variant="h5" color="inherit" gutterBottom>
                      Recuperar Contraseña
                    </Typography>
                  </div>
                </Grid>
              </Grid>
            </Paper>
            <Typography className={classes.subheader} component="h1" variant="h6">
              Credenciales:
            </Typography>
            <TextField
              id="email"
              label="Correo"
              placeholder="usuario@area.uh.cu"
              fullWidth
              margin="normal"
              variant="filled"
              onChange={this.handleChange("email")}
              InputLabelProps={{
                shrink: true,
              }}
            />
            <Button
              type="submit"
              variant="contained"
              color="primary"
              disabled={this.state.loading}
              className={classes.submit}
              style={{marginBottom: 20}}
              onClick={this.getQuestions}
            >
              Recuperar Contraseña
            </Button>
            <div style={{"display": showForm2? "initial" : "none"}}>
              <Typography className={classes.subheader} component="h1" variant="h6">
                Responda las preguntas de seguridad y agregue la nueva contraseña:
              </Typography>
              <TextField
                id="pregunta1"
                label={this.state.pregunta1}
                fullWidth
                margin="normal"
                variant="filled"
                onChange={this.handleChange("respuesta1")}
                InputLabelProps={{
                  shrink: true,
                }}
              />
              <TextField
                id="pregunta2"
                label={this.state.pregunta2}
                fullWidth
                margin="normal"
                variant="filled"
                onChange={this.handleChange("repuesta2")}
                InputLabelProps={{
                  shrink: true,
                }}
              />
              <TextField
                id="password"
                label="Contraseña Nueva"
                fullWidth
                margin="normal"
                variant="filled"
                onChange={this.handleChange("password")}
                InputLabelProps={{
                  shrink: true,
                }}
              />
              <TextField
                id="password2"
                label="Repetir Contraseña Nueva"
                fullWidth
                margin="normal"
                variant="filled"
                onChange={this.handleChange("password2")}
                InputLabelProps={{
                  shrink: true,
                }}
              />
              <Button
              type="submit"
              variant="contained"
              color="primary"
              disabled={this.state.loading}
              className={classes.submit}
            >
              Verificar y guardar contraseña
            </Button>
            </div>
          </main>
        </div>
        {/* Footer */}
        {footer(classes)}
        {/* End footer */}
      </React.Fragment>
    );
  }
}

RecoverPassword.propTypes = {
  classes: PropTypes.object.isRequired,
};

const mapStateToProps = (state) => ({
  loading: state.general.loading
});

export default connect(mapStateToProps, {
  start_loading: passwordActions.start_loading,
  end_loading: passwordActions.end_loading,
})(withStyles(styles)(RecoverPassword));