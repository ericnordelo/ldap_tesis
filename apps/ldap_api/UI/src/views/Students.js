import  React, { Component } from 'react'
import Breadcrumbs from '@material-ui/lab/Breadcrumbs';
import {Link} from 'react-router-dom';
import NavigateNextIcon from '@material-ui/icons/NavigateNext';
import Typography from '@material-ui/core/Typography';
import StudentsTable from '../components/StudentsTable';
import config from '../config';
import CircularIndeterminated from '../components/CircularIndeterminated';

class Students extends Component {
  state = { students: [], loading: true };

  componentDidMount() {
    fetch(config.api_address + '/estudiantes', {credentials: "include"})
      .then(results => results.json())
      .then(data => {
        const ldap_students = data.students;
        if(ldap_students){
          this.setState({ students: ldap_students });
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
          <Typography color="textPrimary">Estudiantes</Typography>
        </Breadcrumbs>
        {this.state.loading ?
          <CircularIndeterminated></CircularIndeterminated> :
          <StudentsTable students={this.state.students} loading={this.state.loading} />
        }
      </div>
    );
  }
}

export default Students;