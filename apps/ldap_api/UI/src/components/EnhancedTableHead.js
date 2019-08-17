import React from 'react';
import PropTypes from 'prop-types';
import TableCell from '@material-ui/core/TableCell';
import TableHead from '@material-ui/core/TableHead';
import TableRow from '@material-ui/core/TableRow';
import TableSortLabel from '@material-ui/core/TableSortLabel';
import Checkbox from '@material-ui/core/Checkbox';
import Tooltip from '@material-ui/core/Tooltip';

class EnhancedTableHead extends React.Component {
    constructor(props){
      super(props)
    }

    createSortHandler = property => event => {
      this.props.onRequestSort(event, property);
    };
  
    render() {
      const { onSelectAllClick, order, orderBy, numSelected, rowCount } = this.props;
      let rows = [];
      if(this.props.workers){
        rows = [
          { id: 'name', numeric: false, disablePadding: true, label: 'Nombre' },
          { id: 'last_name', numeric: false, disablePadding: false, label: 'Apellidos' },
          { id: 'ci', numeric: false, disablePadding: false, label: 'CI' },
          { id: 'area', numeric: false, disablePadding: false, label: 'Área' },
          { id: 'ocupation', numeric: false, disablePadding: false, label: 'Cargo' },
          { id: 'email', numeric: false, disablePadding: false, label: 'Correo' },
        ];
      }else if(this.props.externs){
        rows = [
          { id: 'name', numeric: false, disablePadding: true, label: 'Nombre' },
          { id: 'last_name', numeric: false, disablePadding: false, label: 'Apellidos' },
          { id: 'ci', numeric: false, disablePadding: false, label: 'CI' },
          { id: 'email', numeric: false, disablePadding: false, label: 'Correo' },
        ];
      }else if(this.props.students){
        rows = [
          { id: 'name', numeric: false, disablePadding: true, label: 'Nombre' },
          { id: 'last_name', numeric: false, disablePadding: false, label: 'Apellidos' },
          { id: 'ci', numeric: false, disablePadding: false, label: 'CI' },
          { id: 'faculty', numeric: false, disablePadding: false, label: 'Facultad' },
          { id: 'carrer', numeric: false, disablePadding: false, label: 'Carrera' },
          { id: 'grade', numeric: false, disablePadding: false, label: 'Curso' },
        ];
      }else if(this.props.people){
        rows = [
          { id: 'name', numeric: false, disablePadding: true, label: 'Nombre' },
          { id: 'last_name', numeric: false, disablePadding: false, label: 'Apellidos' },
          { id: 'ci', numeric: false, disablePadding: false, label: 'CI' }
        ];
      }

      return (
        <TableHead>
          <TableRow>
            <TableCell padding="checkbox">
              <Checkbox
                indeterminate={numSelected > 0 && numSelected < rowCount}
                checked={numSelected === rowCount}
                onChange={onSelectAllClick}
              />
            </TableCell>
            {rows.map(
              row => (
                <TableCell
                  key={row.id}
                  align={row.numeric ? 'right' : 'left'}
                  padding={row.disablePadding ? 'none' : 'default'}
                  sortDirection={orderBy === row.id ? order : false}
                >
                  <Tooltip
                    title="Ordenar"
                    placement={row.numeric ? 'bottom-end' : 'bottom-start'}
                    enterDelay={300}
                  >
                    <TableSortLabel
                      active={orderBy === row.id}
                      direction={order}
                      onClick={this.createSortHandler(row.id)}
                    >
                      {row.label}
                    </TableSortLabel>
                  </Tooltip>
                </TableCell>
              ),
              this,
            )}
          </TableRow>
        </TableHead>
      );
    }
  }
  
  EnhancedTableHead.propTypes = {
    numSelected: PropTypes.number.isRequired,
    onRequestSort: PropTypes.func.isRequired,
    onSelectAllClick: PropTypes.func.isRequired,
    order: PropTypes.string.isRequired,
    orderBy: PropTypes.string.isRequired,
    rowCount: PropTypes.number.isRequired,
  };
  
export default EnhancedTableHead;
