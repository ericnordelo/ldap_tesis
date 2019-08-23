import React, {Component} from 'react';
import PropTypes from 'prop-types';
import TextField from '@material-ui/core/TextField';
import Button from '@material-ui/core/Button';
import MenuItem from '@material-ui/core/MenuItem';
import Breadcrumbs from '@material-ui/lab/Breadcrumbs';
import {Link} from 'react-router-dom';
import NavigateNextIcon from '@material-ui/icons/NavigateNext';
import CssBaseline from '@material-ui/core/CssBaseline';
import FormControl from '@material-ui/core/FormControl';
import Input from '@material-ui/core/Input';
import InputLabel from '@material-ui/core/InputLabel';
import Paper from '@material-ui/core/Paper';
import Typography from '@material-ui/core/Typography';
import withStyles from '@material-ui/core/styles/withStyles';
import config from '../config'
import { InputAdornment, Checkbox, FormControlLabel } from '@material-ui/core';
import {connect} from 'react-redux';
import {userActions} from '../actions/authActions';

const styles = theme => ({
  main: {
    width: 'auto',
    display: 'block', // Fix IE 11 issue.
  },
  formControl: {
    margin: theme.spacing.unit,
    minWidth: 180,
  },
  textField: {
    margin: 0,
    minWidth: 180,
    marginRight: '15px'
  },
  paper: {
    marginTop: theme.spacing.unit * 8,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'left',
    padding: `${theme.spacing.unit * 2}px ${theme.spacing.unit * 3}px ${theme.spacing.unit * 3}px`,
  },
  avatar: {
    margin: theme.spacing.unit,
    backgroundColor: theme.palette.secondary.main,
  },
  subheader: {
    marginTop: '20px'
  },
  form: {
    width: '100%', // Fix IE 11 issue.
  },
  submit: {
    marginTop: theme.spacing.unit * 3,
  },
  mr15: {
    marginRight: '15px'
  }
});

const areas = [
  ['imre.uh.cu', 'Instituto de Ciencia y Tecnología de Materiales'],
  ['fcom.uh.cu', 'Facultad de Comunicación'],
  ['ifal.uh.cu', 'Instituto de Farmacia y Alimentos'],
  ['matcom.uh.cu', 'Facultad de Matemática y Computación'],
  ['dict.uh.cu', 'Dirección de Información Científico Técnica'],
  ['geo.uh.cu', 'Facultad de Geografía'],
  ['instec.uh.cu', 'Instituto Superior de Ciencias y Tecnologías Aplicadas'],
  ['direco.uh.cu', 'Dirección de Comunicación'],
  ['flex.uh.cu', 'Facultad de Lenguas Extranjeras'],
  ['iris.uh.cu', 'Dirección Docente de Informatización'],
  ['fisica.uh.cu', 'Facultad de Física'],
  ['lex.uh.cu', 'Facultad de Derecho'],
  ['psico.uh.cu', 'Facultad de Psicología'],
  ['cedem.uh.cu', 'Centro de Estudios Demográficos'],
  ['cepes.uh.cu', 'Centro de Estudios para el Perfeccionamiento de la Educación Superior'],
  ['flacso.uh.cu', 'Facultad Latinoamericana de Ciencias Sociales'],
  ['ceap.uh.cu', 'Centro de Estudios de Administración Pública'],
  ['ffh.uh.cu', 'Facultad de Filosofía e Historia'],
  ['cehseu.uh.cu', 'Centro de Estudios Hemisféricos y sobre los Estados Unidos'],
  ['jbn.uh.cu', 'Jardín Botánico'],
  ['fcf.uh.cu', 'Facultad de Contabilidad y Finanzas'],
  ['ftur.uh.cu', 'Facultad de Turismo'],
  ['fenhi.uh.cu', 'Facultad de Español para no Hispano Hablantes'],
  ['fbio.uh.cu', 'Facultad de Biología'],
  ['cim.uh.cu', 'Centro de Investigaciones Marinas'],
  ['fq.uh.cu', 'Facultad de Química']
]

class AddExtern extends Component{
  
  constructor(props){
    super(props);
    let today = new Date();
    let onMonth = new Date();
    onMonth.setMonth(onMonth.getMonth()+1);
    var dd = today.getDate();
    var mm = today.getMonth() + 1; //January is 0!
    
    var yyyy = today.getFullYear();
    if (dd < 10) {
      dd = '0' + dd;
    } 
    if (mm < 10) {
      mm = '0' + mm;
    }
    today = yyyy + '-' + mm + '-' + dd;
    var dd = onMonth.getDate();
    var mm = onMonth.getMonth() + 1; //January is 0!
    
    var yyyy = onMonth.getFullYear();
    if (dd < 10) {
      dd = '0' + dd;
    } 
    if (mm < 10) {
      mm = '0' + mm;
    }
    onMonth = yyyy + '-' + mm + '-' + dd;
    this.state = {
      name: '',
      lastname1: '',
      lastname2: '',
      ci: '',
      area: 'matcom.uh.cu',
      oldLogin: '',
      hasOldLogin: false,
      beginDate: today,
      endDate: onMonth,
      password: '',
      password2: '',
      hasInternet: false,
      hasChat: false,
      hasEmail: false,
      quota: 0,
      comments: '',
      loading: false
    };
  }
  
  componentDidMount = () => {
    let currentUserIsAdmin = localStorage.getItem('currentUserRole') == 'admin';
    if (!currentUserIsAdmin) {
      this.props.logout();
    }
  }

  handleInputChange = (event) => {
    const { value, name } = event.target;
    this.setState({
      [name]: value
    });
  }
  
  onSubmit = (event) => {
    this.setState({loading: true});
    event.preventDefault();
    
    fetch(config.api_address + '/externos', {
      credentials: "include",
      method: 'POST',
      body: JSON.stringify({
        name: this.state.name, 
        last_name: this.state.lastname1 + ' ' +this.state.lastname2,
        ci: this.state.ci,
        area: this.state.area,
        old_login: this.state.hasOldLogin,
        old_login_email: this.state.oldLogin,
        created_at: this.state.beginDate,
        expires: this.state.endDate,
        internet: this.state.hasInternet,
        quota: this.state.quota,
        chat: this.state.hasChat,
        email: this.state.hasEmail,
        comments: this.state.comments,
        password: this.state.password
      }),
      headers: {
        'Content-Type': 'application/json'
      }
    })
    .then(res => {
      if (res.status === 200) {
        alert('El externo fue agregado satisfactoriamente.');
      } else {
        alert('No se ha podido agregar el externo. Por favor inténtelo de nuevo.');
      }
      this.setState({loading: false});
    })
    .catch(err => {
      console.error(err);
      alert('No se ha podido agregar el externo. Por favor inténtelo de nuevo.');
      this.setState({loading: false});
    });
  }

  handleChange = name => event => {
    this.setState({ [name]: event.target.value });
  };

  render(){
    const { classes } = this.props;

    return (
      <main className={classes.main}>
        <Breadcrumbs separator={<NavigateNextIcon fontSize="small" />} arial-label="Breadcrumb">
          <Link color="inherit" to="/">
            Inicio
          </Link>
          <Link color="inherit" to="/externos">
            Externos
          </Link>
          <Typography color="textPrimary">Agregar Externo</Typography>
        </Breadcrumbs>
        <CssBaseline />
        <Paper className={classes.paper}>
          <Typography component="h1" variant="h5">
            Adicionar personal externo de la UH
          </Typography>
          <form autoComplete="off" className={classes.form} onSubmit={this.onSubmit}>
            <Typography className={classes.subheader} component="h1" variant="h6">
              Datos personales:
            </Typography>
            <div>
              <FormControl className={classes.mr15}>
                <InputLabel
                  htmlFor="name"
                >
                  Nombre
                </InputLabel>
                <Input
                  id="name"
                  value={this.state.name}
                  onChange={this.handleChange("name")}
                />
              </FormControl>
              <FormControl className={classes.mr15}>
                <InputLabel
                  htmlFor="lastname1"
                >
                  1er Apellido
                </InputLabel>
                <Input
                  id="lastname1"
                  value={this.state.lastname1}
                  onChange={this.handleChange("lastname1")}
                />
              </FormControl>
              <FormControl className={classes.mr15}>
                <InputLabel
                  htmlFor="lastname2"
                >
                  2do Apellido
                </InputLabel>
                <Input
                  id="lastname2"
                  value={this.state.lastname2}
                  onChange={this.handleChange("lastname2")}
                />
              </FormControl>
              <FormControl className={classes.mr15}>
                <InputLabel
                  htmlFor="ci"
                >
                  CI
                </InputLabel>
                <Input
                  id="ci"
                  value={this.state.ci}
                  type="number"
                  onChange={this.handleChange("ci")}
                />
              </FormControl>
            </div>
            <Typography className={classes.subheader} component="h1" variant="h6">
              Datos permanentes:
            </Typography>
            <TextField
              required
              id="standard-select-area"
              select
              label="Área"
              className={classes.textField}
              value={this.state.area}
              onChange={this.handleChange('area')}
              SelectProps={{
                MenuProps: {
                  className: classes.menu,
                },
              }}
              margin="normal"
            >
              {areas.map(option => (
                <MenuItem key={option[0]} value={option[0]}>
                  {option[1]}
                </MenuItem>
              ))}
            </TextField>
            <FormControl className={classes.margin}>
              <InputLabel
                htmlFor="has-credentials"
              >
                Viejo Login
              </InputLabel>
              <Input
                startAdornment={(
                  <InputAdornment position="start">
                    <Checkbox
                      checked={this.state.hasOldLogin}
                      onChange={(e) => this.setState({hasOldLogin: e.target.checked})}
                      value="hasOldLogin"
                      style={{padding: 0}}
                    />
                  </InputAdornment>
                )}
                id="has-credentials"
                className={classes.mr15}
                disabled={!this.state.hasOldLogin}
                value={this.state.oldLogin}
                onChange={this.handleChange("oldLogin")}
              />
            </FormControl>
            <FormControl className={classes.mr15}>
              <InputLabel
                htmlFor="password"
              >
                Contraseña
              </InputLabel>
              <Input
                id="password"
                value={this.state.password}
                className={classes.mr15}
                type="password"
                onChange={this.handleChange("password")}
              />
            </FormControl>
            <FormControl className={classes.mr15}>
              <InputLabel
                htmlFor="password2"
              >
                Repita Contraseña
              </InputLabel>
              <Input
                id="password2"
                value={this.state.password2}
                type="password"
                onChange={this.handleChange("password2")}
              />
            </FormControl>
            <Typography className={classes.subheader} component="h1" variant="h6">
             Servicios solicitados:
            </Typography>
            <TextField
              id="beginDate"
              label="Fecha de Inicio"
              type="date"
              value={this.state.beginDate}
              onChange={this.handleChange('beginDate')}
              className={classes.textField}
              InputLabelProps={{
                shrink: true,
              }}
            />
            <TextField
              id="endDate"
              label="Fecha Final"
              type="date"
              value={this.state.endDate}
              onChange={this.handleChange('endDate')}
              className={classes.textField}
              InputLabelProps={{
                shrink: true,
              }}
            />
            <br />
            <br />
            <FormControl className={classes.margin}>
              <InputLabel
                htmlFor="has-internet"
              >
                Internet (quota en MB)
              </InputLabel>
              <Input
                startAdornment={(
                  <InputAdornment position="start">
                    <Checkbox
                      checked={this.state.hasInternet}
                      onChange={(e) => this.setState({hasInternet: e.target.checked})}
                      value="hasInternet"
                      style={{padding: 0}}
                    />
                  </InputAdornment>
                )}
                id="has-internet"
                className={classes.mr15}
                value={this.state.quota}
                disabled={!this.state.hasInternet}
                type="number"
                onChange={this.handleChange("quota")}
              />
            </FormControl>
            <br />
            <FormControlLabel
              control={
                <Checkbox
                  checked={this.state.hasChat}
                  onChange={(e) => this.setState({hasChat: e.target.checked})}
                  value="hasChat"
                />
              }
              label="Chat"
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={this.state.hasEmail}
                  onChange={(e) => this.setState({hasEmail: e.target.checked})}
                  value="hasEmail"
                />
              }
              label="Correo"
            />
            <br />
            <TextField
              id="standard-textarea"
              label="Comentarios"
              placeholder="Esta es una entrada mulilínea"
              multiline
              fullWidth
              margin="normal"
              value={this.state.comments}
              onChange={this.handleChange("comments")}
            />
            <br />
            <Button
              type="submit"
              variant="contained"
              color="primary"
              disabled={this.state.loading}
              className={classes.submit}
            >
              Agregar
            </Button>
          </form>
        </Paper>
      </main>
    );
  }
}

AddExtern.propTypes = {
  classes: PropTypes.object.isRequired,
};

export default connect(() => {}, {logout: userActions.logout})(withStyles(styles)(AddExtern));