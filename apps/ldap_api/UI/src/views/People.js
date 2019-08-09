import  React, { Component } from 'react'
import Breadcrumbs from '@material-ui/lab/Breadcrumbs';
import {Link} from 'react-router-dom';
import NavigateNextIcon from '@material-ui/icons/NavigateNext';
import Typography from '@material-ui/core/Typography';
import PeopleTable from '../components/PeopleTable';
import config from '../config';
import CircularIndeterminated from '../components/CircularIndeterminated';
import Button from '@material-ui/core/Button';
import FiltersDialog from '../components/FiltersDialog';

class People extends Component {
  state = { people: [], loading: true };

  constructor(props){
    super(props);
    this.fetchData = this.fetchData.bind(this);
  }

  componentDidMount() {
    this.fetchData('');
  }

  fetchData(params){
    this.setState({loading: true});
    fetch(config.api_address + '/usuarios' + params, {credentials: "include"})
      .then(results => results.json())
      .then(data => {
        const ldap_people = data.usuarios;
        if(ldap_people){
          this.setState({ people: ldap_people });
        }
        else{
          alert('No se pudieron obtener los trabajadores del API.');
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
          <Typography color="textPrimary">Personas</Typography>
        </Breadcrumbs>

        {this.state.loading ?
          <CircularIndeterminated/> :
          <PeopleTable people={this.state.people} loading={this.state.loading}>
            <FiltersDialog fetchMethod={this.fetchData}/>
            <Button style={{marginLeft: 20}} size="small" onClick={() => this.fetchData('')} variant="outlined" color="primary">
              Limpiar Filtros
            </Button>
          </PeopleTable>
        }
      </div>
    );
  }
}

export default People;