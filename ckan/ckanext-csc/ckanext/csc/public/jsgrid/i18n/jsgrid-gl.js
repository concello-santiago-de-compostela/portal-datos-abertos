(function(jsGrid) {

    jsGrid.locales.gl = {
        grid: {
            noDataContent: "Non encontrado",
            deleteConfirm: "Está seguro?",
            pagerFormat: "{first} {prev} {pages} {next} {last} &nbsp;&nbsp;&nbsp;&nbsp; Páxina {pageIndex} de {pageCount}",
            pagePrevText: "<",
            pageNextText: ">",
            pageFirstText: "<<",
            pageLastText: ">>",
            loadMessage: "Por favor, espere...",
            invalidMessage: "Datos non válidos!"
        },

        loadIndicator: {
            message: "Cargando..."
        },

        fields: {
            control: {
                searchModeButtonTooltip: "Cambiar a procura",
                insertModeButtonTooltip: "Cambiar a inserción",
                editButtonTooltip: "Editar",
                deleteButtonTooltip: "Suprimir",
                searchButtonTooltip: "Procurar",
                clearFilterButtonTooltip: "Borrar filtro",
                insertButtonTooltip: "Inserir",
                updateButtonTooltip: "Actualizar",
                cancelEditButtonTooltip: "Cancelar edición"
            }
        },

        validators: {
            required: { message: "Campo requirido" },
            rangeLength: { message: "A lonxitude do valor está fóra do intervalo definido" },
            minLength: { message: "A lonxitude do valor é demasiado curta" },
            maxLength: { message: "A lonxitude do valor é demasiado longa" },
            pattern: { message: "O valor non se axusta ao patrón definido" },
            range: { message: "Valor fóra do rango definido" },
            min: { message: "Valor demasiado baixo" },
            max: { message: "Valor demasiado alto" }
        }
    };

}(jsGrid, jQuery));
