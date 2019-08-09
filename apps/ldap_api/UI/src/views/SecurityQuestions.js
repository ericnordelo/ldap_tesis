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
import {sections} from './_sections'
import {connect} from 'react-redux'
import {footer} from './_footer'
import {passwordActions} from '../actions/passwordActions'
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

class SecurityQuestions extends Component{

  constructor(props){
    super(props);
    this.state = {
      email: '',
      password: '',
      pregunta1: '',
      respuesta1: '',
      pregunta2: '',
      respuesta2: '',
      loading: false
    };
  }

  getQuestions = (event) => {
    event.preventDefault();

    if(this.state.password === ''){
      alert('La contraseña no puede estar en blanco.');
      return;
    }

    this.props.start_loading();

    fetch(config.api_address + '/p/preguntasdeseguridad', {
        credentials: "include",
        method: 'PATCH',
        body: JSON.stringify({
          email: this.state.email,
          password: this.state.password
        }),
        headers: {
          'Content-Type': 'application/json'
        }
    })
    .then(res => res.json())
    .then(data => {
        if(data.error === 'No tiene preguntas de seguridad'){
          alert('No tiene preguntas de seguridad agregadas.');
        } else if(data.error){
          alert('Sus credenciales son incorrectas.');
        }
        else{
          this.setState({pregunta1: data.preguntas[0], pregunta2: data.preguntas[1], respuesta1: data.respuestas[0], respuesta2: data.respuestas[1]})
        }
        this.props.end_loading();
    })
    .catch(err => {
        this.props.end_loading();
        console.error(err);
        alert('Sus credenciales son incorrectas.');
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

  handleChange = name => event => {
    this.setState({ [name]: event.target.value });
  };

  render(){
    const {classes} = this.props;

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
                      Adicionar Preguntas y Repuestas de Seguridad
                    </Typography>
                  </div>
                </Grid>
              </Grid>
            </Paper>
            <form autoComplete="off" className={classes.form} onSubmit={this.onSubmit}>
              <Grid container spacing={3}>
                <Grid item md={6} xs={12} style={{paddingRight: 8}}>
                  <Typography className={classes.subheader} component="h1" variant="h6">
                    Credenciales:
                  </Typography>
                  <TextField
                    id="email"
                    label="Correo"
                    placeholder="usuario@area.uh.cu"
                    fullWidth
                    margin="normal"
                    onChange={this.handleChange("email")}
                    variant="filled"
                    InputLabelProps={{
                      shrink: true,
                    }}
                  />
                  <TextField
                    id="password"
                    type="password"
                    label="Contraseña"
                    fullWidth
                    margin="normal"
                    variant="filled"
                    onChange={this.handleChange("password")}
                    InputLabelProps={{
                      shrink: true,
                    }}
                  />
                  <Button
                    type="submit"
                    variant="contained"
                    color="primary"
                    disabled={this.props.loading}
                    className={classes.submit}
                    onClick={this.getQuestions}
                  >
                    Chequear preguntas y respuestas
                  </Button>
                </Grid>
                <Grid item md={6} xs={12}>
                  <Typography className={classes.subheader} component="h1" variant="h6">
                    Preguntas y Respuestas:
                  </Typography>
                  <TextField
                    id="pregunta1"
                    label="Pregunta 1"
                    fullWidth
                    margin="normal"
                    variant="filled"
                    value={this.state.pregunta1}
                    onChange={this.handleChange("pregunta1")}
                    InputLabelProps={{
                      shrink: true,
                    }}
                  />
                  <TextField
                    id="respuesta1"
                    label="Respuesta 1"
                    fullWidth
                    margin="normal"
                    variant="filled"
                    value={this.state.respuesta1}
                    onChange={this.handleChange("respuesta1")}
                    InputLabelProps={{
                      shrink: true,
                    }}
                  />
                  <TextField
                    id="pregunta2"
                    label="Pregunta 2"
                    fullWidth
                    margin="normal"
                    variant="filled"
                    value={this.state.pregunta2}
                    onChange={this.handleChange("pregunta2")}
                    InputLabelProps={{
                      shrink: true,
                    }}
                  />
                  <TextField
                    id="respuesta2"
                    label="Respuesta 2"
                    fullWidth
                    margin="normal"
                    value={this.state.respuesta2}
                    onChange={this.handleChange("respuesta2")}
                    variant="filled"
                    InputLabelProps={{
                      shrink: true,
                    }}
                  />
                  <Button
                    type="submit"
                    variant="contained"
                    color="primary"
                    className={classes.submit}
                    disabled={this.props.loading}
                    onClick={this.setQuestions}
                  >
                    Guardar preguntas y respuestas
                  </Button>
                </Grid>
              </Grid>
            </form>
          
          </main>
        </div>
        {/* Footer */}
        {footer(classes)}
        {/* End footer */}
      </React.Fragment>
    );
  }
}

SecurityQuestions.propTypes = {
  classes: PropTypes.object.isRequired,
};

const mapStateToProps = (state) => ({
  loading: state.general.loading
});

export default connect(mapStateToProps, {
  start_loading: passwordActions.start_loading,
  end_loading: passwordActions.end_loading,
})(withStyles(styles)(SecurityQuestions));