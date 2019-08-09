import React, { Component } from 'react'
import Breadcrumbs from '@material-ui/lab/Breadcrumbs';
import { Link } from 'react-router-dom';
import NavigateNextIcon from '@material-ui/icons/NavigateNext';
import Typography from '@material-ui/core/Typography';
import WorkersTable from '../components/WorkersTable';
import config from '../config';
import CircularIndeterminated from '../components/CircularIndeterminated';
import FiltersDialog from '../components/FiltersDialog';

class Workers extends Component {
  state = { workers: [], loading: true };

  componentDidMount() {
    fetch(config.api_address + '/trabajadores', { credentials: "include" })
      .then(results => results.json())
      .then(data => {
        const ldap_workers = data.workers;
        if (ldap_workers) {
          this.setState({ workers: ldap_workers });
        }
        else {
          alert('No se pudieron obtener los trabajadores del API.');
        }
        this.setState({ loading: false });
      }).catch(err => {
        console.log(err);
        this.setState({ loading: false });
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
            <FiltersDialog/>
          </WorkersTable>
        }
      </div>
    );
  }
}

export default Workers;