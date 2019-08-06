import React from 'react';
import Button from '@material-ui/core/Button';
import TextField from '@material-ui/core/TextField';
import Dialog from '@material-ui/core/Dialog';
import DialogActions from '@material-ui/core/DialogActions';
import DialogContent from '@material-ui/core/DialogContent';
import DialogTitle from '@material-ui/core/DialogTitle';

export default class FiltersDialog extends React.Component {
  constructor(props){
    super(props);

    this.state = {
      open: false,
      name: '',
      last_name: '',
      email: '',
    }
  }

  handleChange = name => event => {
    this.setState({ [name]: event.target.value });
  };

  handleClickOpen = () => {
    this.setState({ open: true });
  }

  handleClose = () => {
    this.setState({ open: false });
  }

  handleFilter = () => {
    let params = '';
    if(this.state.name.length > 0){
      if(!params.startsWith('?')){
        params = '?nombre=' + this.state.name;
      }else{
        params += '&nombre=' + this.state.name;
      }
    }
    if(this.state.last_name.length > 0){
      if(!params.startsWith('?')){
        params = '?apellidos=' + this.state.last_name;
      }else{
        params += '&apellidos=' + this.state.last_name;
      }
    }
    if(this.state.email.length > 0){
      if(!params.startsWith('?')){
        params = '?correo=' + this.state.email;
      }else{
        params += '&correo=' + this.state.email;
      }
    }
    this.props.fetchMethod(params);
  }

  render() {
    return (
      <div style={{display: 'inline', marginLeft: 20}}>
        <Button size="small" variant="outlined" color="primary" onClick={this.handleClickOpen}>
          Abrir formulario de filtros
        </Button>
        <Dialog
          fullWidth
          open={this.state.open}
          onClose={this.handleClose}
          aria-labelledby="form-dialog-title"
        >
          <DialogTitle id="form-dialog-title">Filtros de Externos</DialogTitle>
          <DialogContent>
            <TextField
              margin="dense"
              id="name"
              label="Nombre"
              value={this.state.name}
              onChange={this.handleChange("name")}
            />
            <TextField
              style={{marginLeft: 20}}
              margin="dense"
              id="last_name"
              label="Apellidos"
              onChange={this.handleChange("last_name")}
            />
            <TextField
              margin="dense"
              id="email"
              label="Correo"
              type="email"
              onChange={this.handleChange("email")}
              fullWidth
            />
            <TextField
              id="date"
              label="Creación (Desde) "
              type="date"
              style={{marginTop: 8}}
              InputLabelProps={{
                shrink: true,
              }}
            />
            <TextField
              id="date"
              label="Creación (Hasta)"
              type="date"
              style={{marginTop: 8, marginLeft: 20}}
              InputLabelProps={{
                shrink: true,
              }}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={this.handleClose} color="secondary">
              Cancelar
            </Button>
            <Button onClick={this.handleFilter} color="primary">
              Filtrar
            </Button>
          </DialogActions>
        </Dialog>
      </div>
    )
  }
}