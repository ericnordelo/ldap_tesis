import  React, { Component } from 'react'
import Breadcrumbs from '@material-ui/lab/Breadcrumbs';
import {Link} from 'react-router-dom';
import NavigateNextIcon from '@material-ui/icons/NavigateNext';
import Typography from '@material-ui/core/Typography';
import Button from '@material-ui/core/Button';
import ExternsTable from '../components/ExternsTable';
import config from '../config';
import CircularIndeterminated from '../components/CircularIndeterminated';
import ExternsFiltersDialog from '../components/ExternsFiltersDialog';
import {connect} from 'react-redux'
import {userActions} from '../actions/authActions'


class Externs extends Component {
  state = { 
    externs: [], 
    loading: true,
    name: '',
    last_name: '',
    email: '',
  };
  constructor(props){
    super(props);
    this.fetchData = this.fetchData.bind(this);
  }

  componentDidMount() {
    this.fetchData('', '', '', '');
  }

  fetchData(params, name, last_name, email){
    this.setState({loading: true, name: name, last_name: last_name, email: email});
    fetch(config.api_address + '/externos' + params, {credentials: "include"})
      .then(results => results.json())
      .then(data => {
        const ldap_externs = data.externs;
        if(ldap_externs){
          this.setState({ externs: ldap_externs });
        }
        else{
          alert('Su sesión ha expirado.');
          this.props.logout();
        }
        this.setState({loading: false});
      }).catch(err => {
        console.log(err);
        this.setState({loading: false});
      })
  }

  render() {
    let currentUserIsAdmin = localStorage.getItem('currentUserRole') == 'admin' 

    return (
      <div>
        <Breadcrumbs separator={<NavigateNextIcon fontSize="small" />} arial-label="Breadcrumb">
          <Link color="inherit" to="/">
            Inicio
          </Link>
          <Typography color="textPrimary">Externos</Typography>
        </Breadcrumbs>
        {this.state.loading ?
          <CircularIndeterminated></CircularIndeterminated> :
          <ExternsTable externs={this.state.externs} loading={this.state.loading}>
            <ExternsFiltersDialog name={this.state.name} last_name={this.state.last_name} email={this.state.email} fetchMethod={this.fetchData}/>
            <Button style={{marginLeft: 20}} to="/externos/agregar" size="small" onClick={() => this.fetchData('', '', '', '')} variant="outlined" color="primary">
              Limpiar Filtros
            </Button>
            {currentUserIsAdmin ? 
              <Button style={{marginLeft: 20}} to="/externos/agregar" size="small" component={Link} variant="contained" color="primary">
              Agregar Externo
            </Button> : ''}
            
          </ExternsTable>
        }
      </div>
    );
  }
}

export default connect(() => {}, {logout: userActions.logout})(Externs);