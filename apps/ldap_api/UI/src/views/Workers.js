import React, { Component } from 'react'
import Breadcrumbs from '@material-ui/lab/Breadcrumbs';
import { Link } from 'react-router-dom';
import NavigateNextIcon from '@material-ui/icons/NavigateNext';
import Typography from '@material-ui/core/Typography';
import WorkersTable from '../components/WorkersTable';
import Button from '@material-ui/core/Button';
import config from '../config';
import CircularIndeterminated from '../components/CircularIndeterminated';
import FiltersDialog from '../components/FiltersDialog';

class Workers extends Component {
  state = { workers: [], loading: true };

  constructor(props){
    super(props);
    this.fetchData = this.fetchData.bind(this);
  }

  componentDidMount() {
    this.fetchData('');
  }

  fetchData(params){
    this.setState({loading: true});
    fetch(config.api_address + '/trabajadores' + params, {credentials: "include"})
      .then(results => results.json())
      .then(data => {
        const ldap_workers = data.workers;
        if(ldap_workers){
          this.setState({ workers: ldap_workers });
        }
        else{
          alert('No se pudieron obtener los trabajadores del API.')
        }
        this.setState({loading: false});
      }).catch(err => {
        console.log(err);
        this.setState({loading: false});
      })
  }

  render() {
    return (
      <div>
        <Breadcrumbs separator={<NavigateNextIcon fontSize="small" />} arial-label="Breadcrumb">
          <Link color="inherit" to="/">
            Inicio
          </Link>
          <Typography color="textPrimary">Trabajadores</Typography>
        </Breadcrumbs>
        
        {this.state.loading ?
          <CircularIndeterminated/> :
          <WorkersTable workers={this.state.workers} loading={this.state.loading}>
            <FiltersDialog fetchMethod={this.fetchData}/>
            <Button style={{marginLeft: 20}} to="/externos/agregar" size="small" onClick={() => this.fetchData('')} variant="outlined" color="primary">
              Limpiar Filtros
            </Button> 
          </WorkersTable>
        }
      </div>
    );
  }
}

export default Workers;