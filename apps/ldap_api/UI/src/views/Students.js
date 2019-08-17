import  React, { Component } from 'react'
import Breadcrumbs from '@material-ui/lab/Breadcrumbs';
import {Link} from 'react-router-dom';
import NavigateNextIcon from '@material-ui/icons/NavigateNext';
import Typography from '@material-ui/core/Typography';
import Button from '@material-ui/core/Button';
import StudentsTable from '../components/StudentsTable';
import config from '../config';
import CircularIndeterminated from '../components/CircularIndeterminated';
import FiltersDialog from '../components/FiltersDialog';

class Students extends Component {
  state = { 
    students: [], 
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
    fetch(config.api_address + '/estudiantes' + params, {credentials: "include"})
      .then(results => results.json())
      .then(data => {
        const ldap_students = data.students;
        if(ldap_students){
          this.setState({ students: ldap_students });
        }
        else{
          alert('No se pudieron obtener los estudiantes del API.')
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
          <Typography color="textPrimary">Estudiantes</Typography>
        </Breadcrumbs>
        {this.state.loading ?
          <CircularIndeterminated></CircularIndeterminated> :
          <StudentsTable students={this.state.students} loading={this.state.loading}>
            <FiltersDialog name={this.state.name} last_name={this.state.last_name} email={this.state.email} fetchMethod={this.fetchData}/>
            <Button style={{marginLeft: 20}} to="/externos/agregar" size="small" onClick={() => this.fetchData('', '', '', '')} variant="outlined" color="primary">
              Limpiar Filtros
            </Button> 
          </StudentsTable>
        }
      </div>
    );
  }
}

export default Students;