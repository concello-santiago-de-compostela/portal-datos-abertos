(function(jsGrid) {

    jsGrid.locales.ca = {
        grid: {
            noDataContent: "No s’ha trobat",
            deleteConfirm: "N’esteu segur?",
            pagerFormat: ": {first} {prev} {pages} {next} {last} &nbsp;&nbsp; {pageIndex} de {pageCount}",
            pagerFormat: "{first} {prev} {pages} {next} {last} &nbsp;&nbsp;&nbsp;&nbsp; Pàgina {pageIndex} de {pageCount}",
            pagePrevText: "<",
            pageNextText: ">",
            pageFirstText: "<<",
            pageLastText: ">>",
            loadMessage: "Si us plau, espereu...",
            invalidMessage: "¡Dades no vàlides!"
        },

        loadIndicator: {
            message: "Carregant..."
        },

        fields: {
            control: {
                searchModeButtonTooltip: "Canvia a cerca",
                insertModeButtonTooltip: "Canvia a inserció",
                editButtonTooltip: "Edita",
                deleteButtonTooltip: "Suprimeix",
                searchButtonTooltip: "Cerca",
                clearFilterButtonTooltip: "Esborra el filtre",
                insertButtonTooltip: "Insereix",
                updateButtonTooltip: "Actualitza",
                cancelEditButtonTooltip: "Cancel·la l’edició"
            }
        },

        validators: {
            required: { message: "Camp requerit" },
            rangeLength: { message: "La longitud del valor és fora de l'interval definit" },
            minLength: { message: "La longitud del valor és massa curta" },
            maxLength: { message: "La longitud del valor és massa llarga" },
            pattern: { message: "El valor no s'ajusta al patró definit" },
            range: { message: "Valor fora del rang definit" },
            min: { message: "Valor massa baix" },
            max: { message: "Valor massa alt" }
        }
    };

}(jsGrid, jQuery));
